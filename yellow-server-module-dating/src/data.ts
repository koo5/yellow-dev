import { newLogger, DataGeneric } from 'yellow-server-common';
import { Mutex } from 'async-mutex';

let Log = newLogger('data');

interface Profile {
 userId: number;
 displayName: string;
 bio: string;
 birthdate: string;
 gender: string;
 lookingFor: string;
 location: string;
 interests: string[];
 photos: string[];
 created: Date;
 updated: Date;
}

interface Like {
 id: number;
 fromUserId: number;
 toUserId: number;
 created: Date;
}

interface Match {
 id: number;
 user1Id: number;
 user2Id: number;
 created: Date;
}

class Data extends DataGeneric {
 profileMutex: Mutex;
 
 constructor(settings: any) {
  super(settings);
  this.profileMutex = new Mutex();
 }

 async createDB(): Promise<void> {
  try {
   await this.db.query(`
    CREATE TABLE IF NOT EXISTS profiles (
     user_id INT PRIMARY KEY,
     display_name VARCHAR(255) NOT NULL,
     bio TEXT,
     birthdate DATE,
     gender VARCHAR(50),
     looking_for VARCHAR(50),
     location VARCHAR(255),
     interests JSON,
     photos JSON,
     created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
   `);

   await this.db.query(`
    CREATE TABLE IF NOT EXISTS likes (
     id INT PRIMARY KEY AUTO_INCREMENT,
     from_user_id INT NOT NULL,
     to_user_id INT NOT NULL,
     created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     UNIQUE KEY unique_like (from_user_id, to_user_id)
    )
   `);

   await this.db.query(`
    CREATE TABLE IF NOT EXISTS matches (
     id INT PRIMARY KEY AUTO_INCREMENT,
     user1_id INT NOT NULL,
     user2_id INT NOT NULL,
     created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
     UNIQUE KEY unique_match (user1_id, user2_id)
    )
   `);
  } catch (ex) {
   Log.error('Error creating database tables', ex);
   process.exit(1);
  }
 }

 async getUserProfile(userId: number): Promise<Profile | null> {
  try {
   const result = await this.db.query(
    'SELECT * FROM profiles WHERE user_id = ?',
    [userId]
   );

   if (result.length === 0) {
    return null;
   }

   const profile = result[0];
   return {
    userId: profile.user_id,
    displayName: profile.display_name,
    bio: profile.bio,
    birthdate: profile.birthdate,
    gender: profile.gender,
    lookingFor: profile.looking_for,
    location: profile.location,
    interests: JSON.parse(profile.interests || '[]'),
    photos: JSON.parse(profile.photos || '[]'),
    created: profile.created,
    updated: profile.updated
   };
  } catch (error) {
   Log.error('Error getting user profile', error);
   throw error;
  }
 }

 async updateUserProfile(userId: number, profileData: Partial<Profile>): Promise<Profile> {
  return await this.profileMutex.runExclusive(async () => {
   try {
    const existingProfile = await this.getUserProfile(userId);
    
    if (!existingProfile) {
     // Create new profile
     await this.db.query(
      `INSERT INTO profiles 
       (user_id, display_name, bio, birthdate, gender, looking_for, location, interests, photos)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
      [
       userId,
       profileData.displayName || '',
       profileData.bio || '',
       profileData.birthdate || null,
       profileData.gender || '',
       profileData.lookingFor || '',
       profileData.location || '',
       JSON.stringify(profileData.interests || []),
       JSON.stringify(profileData.photos || [])
      ]
     );
    } else {
     // Update existing profile
     const updates = [];
     const values = [];

     if (profileData.displayName !== undefined) {
      updates.push('display_name = ?');
      values.push(profileData.displayName);
     }

     if (profileData.bio !== undefined) {
      updates.push('bio = ?');
      values.push(profileData.bio);
     }

     if (profileData.birthdate !== undefined) {
      updates.push('birthdate = ?');
      values.push(profileData.birthdate);
     }

     if (profileData.gender !== undefined) {
      updates.push('gender = ?');
      values.push(profileData.gender);
     }

     if (profileData.lookingFor !== undefined) {
      updates.push('looking_for = ?');
      values.push(profileData.lookingFor);
     }

     if (profileData.location !== undefined) {
      updates.push('location = ?');
      values.push(profileData.location);
     }

     if (profileData.interests !== undefined) {
      updates.push('interests = ?');
      values.push(JSON.stringify(profileData.interests));
     }

     if (profileData.photos !== undefined) {
      updates.push('photos = ?');
      values.push(JSON.stringify(profileData.photos));
     }

     if (updates.length > 0) {
      await this.db.query(
       `UPDATE profiles SET ${updates.join(', ')} WHERE user_id = ?`,
       [...values, userId]
      );
     }
    }

    // Return the updated profile
    return await this.getUserProfile(userId);
   } catch (error) {
    Log.error('Error updating user profile', error);
    throw error;
   }
  });
 }

 async searchProfiles(userId: number, searchParams: any): Promise<Profile[]> {
  try {
   let query = 'SELECT * FROM profiles WHERE user_id != ?';
   const queryParams = [userId];

   // Add filters based on search parameters
   if (searchParams.gender) {
    query += ' AND gender = ?';
    queryParams.push(searchParams.gender);
   }

   if (searchParams.minAge && searchParams.maxAge) {
    query += ' AND birthdate BETWEEN DATE_SUB(CURDATE(), INTERVAL ? YEAR) AND DATE_SUB(CURDATE(), INTERVAL ? YEAR)';
    queryParams.push(searchParams.maxAge, searchParams.minAge);
   } else if (searchParams.minAge) {
    query += ' AND birthdate <= DATE_SUB(CURDATE(), INTERVAL ? YEAR)';
    queryParams.push(searchParams.minAge);
   } else if (searchParams.maxAge) {
    query += ' AND birthdate >= DATE_SUB(CURDATE(), INTERVAL ? YEAR)';
    queryParams.push(searchParams.maxAge);
   }

   if (searchParams.location) {
    query += ' AND location LIKE ?';
    queryParams.push(`%${searchParams.location}%`);
   }

   // Add pagination
   const limit = searchParams.limit || 20;
   const offset = searchParams.offset || 0;
   query += ' LIMIT ? OFFSET ?';
   queryParams.push(limit, offset);

   const results = await this.db.query(query, queryParams);

   return results.map(profile => ({
    userId: profile.user_id,
    displayName: profile.display_name,
    bio: profile.bio,
    birthdate: profile.birthdate,
    gender: profile.gender,
    lookingFor: profile.looking_for,
    location: profile.location,
    interests: JSON.parse(profile.interests || '[]'),
    photos: JSON.parse(profile.photos || '[]'),
    created: profile.created,
    updated: profile.updated
   }));
  } catch (error) {
   Log.error('Error searching profiles', error);
   throw error;
  }
 }

 async likeProfile(fromUserId: number, toUserId: number): Promise<{ isMatch: boolean }> {
  try {
   // Check if the target user has already liked the current user
   const existingLike = await this.db.query(
    'SELECT * FROM likes WHERE from_user_id = ? AND to_user_id = ?',
    [toUserId, fromUserId]
   );

   // Record the like
   try {
    await this.db.query(
     'INSERT INTO likes (from_user_id, to_user_id) VALUES (?, ?)',
     [fromUserId, toUserId]
    );
   } catch (err) {
    // If the like already exists, just continue
    if (err.code !== 'ER_DUP_ENTRY') {
     throw err;
    }
   }

   // If there's a mutual like, create a match
   if (existingLike.length > 0) {
    try {
     // Ensure user1_id is always the smaller ID for consistency
     const user1Id = Math.min(fromUserId, toUserId);
     const user2Id = Math.max(fromUserId, toUserId);
     
     await this.db.query(
      'INSERT INTO matches (user1_id, user2_id) VALUES (?, ?)',
      [user1Id, user2Id]
     );
     
     return { isMatch: true };
    } catch (err) {
     // If the match already exists, just return true
     if (err.code === 'ER_DUP_ENTRY') {
      return { isMatch: true };
     }
     throw err;
    }
   }

   return { isMatch: false };
  } catch (error) {
   Log.error('Error liking profile', error);
   throw error;
  }
 }

 async getUserLikes(userId: number): Promise<{ received: any[], sent: any[] }> {
  try {
   // Get likes received by the user
   const receivedLikes = await this.db.query(`
    SELECT l.*, p.display_name, p.photos
    FROM likes l
    JOIN profiles p ON l.from_user_id = p.user_id
    WHERE l.to_user_id = ?
   `, [userId]);

   // Get likes sent by the user
   const sentLikes = await this.db.query(`
    SELECT l.*, p.display_name, p.photos
    FROM likes l
    JOIN profiles p ON l.to_user_id = p.user_id
    WHERE l.from_user_id = ?
   `, [userId]);

   return {
    received: receivedLikes.map(like => ({
     id: like.id,
     fromUserId: like.from_user_id,
     displayName: like.display_name,
     photo: JSON.parse(like.photos || '[]')[0] || null,
     created: like.created
    })),
    sent: sentLikes.map(like => ({
     id: like.id,
     toUserId: like.to_user_id,
     displayName: like.display_name,
     photo: JSON.parse(like.photos || '[]')[0] || null,
     created: like.created
    }))
   };
  } catch (error) {
   Log.error('Error getting user likes', error);
   throw error;
  }
 }

 async getUserMatches(userId: number): Promise<any[]> {
  try {
   // Get all matches for the user
   const matches = await this.db.query(`
    SELECT m.*, 
     CASE 
      WHEN m.user1_id = ? THEN m.user2_id 
      ELSE m.user1_id 
     END AS matched_user_id,
     p.display_name, p.photos
    FROM matches m
    JOIN profiles p ON (
     CASE 
      WHEN m.user1_id = ? THEN m.user2_id 
      ELSE m.user1_id 
     END = p.user_id
    )
    WHERE m.user1_id = ? OR m.user2_id = ?
    ORDER BY m.created DESC
   `, [userId, userId, userId, userId]);

   return matches.map(match => ({
    id: match.id,
    matchedUserId: match.matched_user_id,
    displayName: match.display_name,
    photo: JSON.parse(match.photos || '[]')[0] || null,
    created: match.created
   }));
  } catch (error) {
   Log.error('Error getting user matches', error);
   throw error;
  }
 }
}

export default Data;
