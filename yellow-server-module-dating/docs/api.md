# Yellow Server Module Dating API Documentation

This document describes the API endpoints available in the Yellow Server Module Dating.

## WebSocket API

All API calls are made through WebSocket connections. The general format for requests is:

```json
{
  "type": "request",
  "requestID": "unique-request-id",
  "data": {
    "command": "command_name",
    "params": {
      // command-specific parameters
    }
  }
}
```

Responses follow this format:

```json
{
  "type": "response",
  "requestID": "unique-request-id",
  "error": false, // or error code number
  "message": "Success message or error description",
  // Additional data specific to the command
}
```

## Available Commands

### Profile Operations

#### `profile_get`
Get the current user's profile.

**Parameters:** None

**Response:**
- Success: `{ "error": false, "data": { "profile": {...} } }`
- Error: Error object with code and message

#### `profile_update`
Update the current user's profile.

**Parameters:**
- `profile` (object): Profile data to update
  - `displayName` (string, optional): User's display name
  - `bio` (string, optional): User's biography
  - `birthdate` (string, optional): User's birthdate in YYYY-MM-DD format
  - `gender` (string, optional): User's gender
  - `lookingFor` (string, optional): Gender preference
  - `location` (string, optional): User's location
  - `interests` (array, optional): Array of user's interests
  - `photos` (array, optional): Array of photo URLs

**Response:**
- Success: `{ "error": false, "message": "Profile updated successfully", "data": { "profile": {...} } }`
- Error: Error object with code and message

#### `profile_search`
Search for profiles based on criteria.

**Parameters:**
- `searchParams` (object): Search parameters
  - `gender` (string, optional): Filter by gender
  - `minAge` (number, optional): Minimum age
  - `maxAge` (number, optional): Maximum age
  - `location` (string, optional): Filter by location
  - `limit` (number, optional): Maximum number of results (default: 20)
  - `offset` (number, optional): Pagination offset (default: 0)

**Response:**
- Success: `{ "error": false, "data": { "profiles": [...] } }`
- Error: Error object with code and message

### Interaction Operations

#### `like_profile`
Like another user's profile.

**Parameters:**
- `targetUserId` (number): ID of the user to like

**Response:**
- Success: `{ "error": false, "message": "Like recorded", "data": { "isMatch": false } }`
- Success (match): `{ "error": false, "message": "Match created!", "data": { "isMatch": true } }`
- Error: Error object with code and message

#### `get_likes`
Get the list of likes received and sent by the current user.

**Parameters:** None

**Response:**
- Success: `{ "error": false, "data": { "likes": { "received": [...], "sent": [...] } } }`
- Error: Error object with code and message

#### `get_matches`
Get the list of matches for the current user.

**Parameters:** None

**Response:**
- Success: `{ "error": false, "data": { "matches": [...] } }`
- Error: Error object with code and message

## Events

The following events can be subscribed to using the `subscribe` command:

- `profile_update`: Triggered when the user's profile is updated
- `match_notification`: Triggered when a new match is created
- `like_notification`: Triggered when someone likes the user's profile

### Subscribing to Events

**Request:**
```json
{
  "type": "request",
  "requestID": "unique-request-id",
  "data": {
    "command": "subscribe",
    "params": {
      "event": "event_name"
    }
  }
}
```

**Response:**
```json
{
  "type": "response",
  "requestID": "unique-request-id",
  "error": false,
  "message": "Event subscribed"
}
```

### Unsubscribing from Events

**Request:**
```json
{
  "type": "request",
  "requestID": "unique-request-id",
  "data": {
    "command": "unsubscribe",
    "params": {
      "event": "event_name"
    }
  }
}
```

**Response:**
```json
{
  "type": "response",
  "requestID": "unique-request-id",
  "error": false,
  "message": "Event unsubscribed"
}
```
