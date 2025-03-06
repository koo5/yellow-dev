import { ModuleApiBase, newLogger } from 'yellow-server-common';
import { Mutex } from 'async-mutex';

let Log = newLogger('api-client');

export class ApiClient extends ModuleApiBase {
 profile_mutex: Mutex;

 constructor(app) {
  super(app, ['profile_update', 'match_notification', 'like_notification']);
  this.commands = {
   ...this.commands,
   profile_get: { method: this.profile_get.bind(this), reqUserSession: true },
   profile_update: { method: this.profile_update.bind(this), reqUserSession: true },
   profile_search: { method: this.profile_search.bind(this), reqUserSession: true },
   like_profile: { method: this.like_profile.bind(this), reqUserSession: true },
   get_likes: { method: this.get_likes.bind(this), reqUserSession: true },
   get_matches: { method: this.get_matches.bind(this), reqUserSession: true }
  };
  this.profile_mutex = new Mutex();
 }

 async profile_get(c) {
  try {
   const profile = await this.app.data.getUserProfile(c.userID);
   return { error: false, data: { profile } };
  } catch (err) {
   Log.error('Error getting profile', err);
   return { error: 'PROFILE_GET_ERROR', message: 'Error retrieving profile' };
  }
 }

 async profile_update(c) {
  if (!c.params) return { error: 'PARAMETERS_MISSING', message: 'Parameters are missing' };
  if (!c.params.profile) return { error: 'PROFILE_DATA_MISSING', message: 'Profile data is missing' };

  try {
   const result = await this.profile_mutex.runExclusive(async () => {
    const updatedProfile = await this.app.data.updateUserProfile(c.userID, c.params.profile);
    return updatedProfile;
   });

   this.signals.notifyUser(c.userID, 'profile_update', { profile: result });
   return { error: false, message: 'Profile updated successfully', data: { profile: result } };
  } catch (err) {
   Log.error('Error updating profile', err);
   return { error: 'PROFILE_UPDATE_ERROR', message: 'Error updating profile' };
  }
 }

 async profile_search(c) {
  if (!c.params) return { error: 'PARAMETERS_MISSING', message: 'Parameters are missing' };
  
  try {
   const searchParams = c.params.searchParams || {};
   const profiles = await this.app.data.searchProfiles(c.userID, searchParams);
   return { error: false, data: { profiles } };
  } catch (err) {
   Log.error('Error searching profiles', err);
   return { error: 'PROFILE_SEARCH_ERROR', message: 'Error searching profiles' };
  }
 }

 async like_profile(c) {
  if (!c.params) return { error: 'PARAMETERS_MISSING', message: 'Parameters are missing' };
  if (!c.params.targetUserId) return { error: 'TARGET_USER_MISSING', message: 'Target user ID is missing' };

  try {
   const targetUserId = c.params.targetUserId;
   const result = await this.app.data.likeProfile(c.userID, targetUserId);
   
   // Notify the target user about the like
   this.signals.notifyUser(targetUserId, 'like_notification', { 
    fromUserId: c.userID,
    timestamp: new Date().toISOString()
   });

   // If this created a match, notify both users
   if (result.isMatch) {
    this.signals.notifyUser(c.userID, 'match_notification', { 
     matchedUserId: targetUserId,
     timestamp: new Date().toISOString()
    });
    
    this.signals.notifyUser(targetUserId, 'match_notification', { 
     matchedUserId: c.userID,
     timestamp: new Date().toISOString()
    });
   }

   return { 
    error: false, 
    message: result.isMatch ? 'Match created!' : 'Like recorded', 
    data: { isMatch: result.isMatch } 
   };
  } catch (err) {
   Log.error('Error liking profile', err);
   return { error: 'LIKE_PROFILE_ERROR', message: 'Error liking profile' };
  }
 }

 async get_likes(c) {
  try {
   const likes = await this.app.data.getUserLikes(c.userID);
   return { error: false, data: { likes } };
  } catch (err) {
   Log.error('Error getting likes', err);
   return { error: 'GET_LIKES_ERROR', message: 'Error retrieving likes' };
  }
 }

 async get_matches(c) {
  try {
   const matches = await this.app.data.getUserMatches(c.userID);
   return { error: false, data: { matches } };
  } catch (err) {
   Log.error('Error getting matches', err);
   return { error: 'GET_MATCHES_ERROR', message: 'Error retrieving matches' };
  }
 }
}
