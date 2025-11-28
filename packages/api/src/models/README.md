# MongoDB Data Models

This directory contains MongoDB schema definitions and models for the Chimera Analytics system.

## Models

### User Profile (`user.ts`)
- User authentication and profile information
- API key management
- User preferences and settings
- Expertise level tracking
- **Requirements**: 8.1, 8.3, 10.1, 11.1

**Indexes**:
- `userId` (unique)
- `email` (unique)
- `apiKeys.key` (sparse)
- `createdAt`

### Dashboard (`dashboard.ts`)
- Dashboard configuration and layout
- Widget definitions and positioning
- Sharing and collaboration settings
- **Requirements**: 8.1, 8.3

**Indexes**:
- `dashboardId` (unique)
- `userId`
- `userId + createdAt` (compound)
- `shared`
- `tags`

### Report (`report.ts`)
- Generated report documents
- Analysis results and visualizations
- Fact-checking results
- **TTL Index**: Automatic expiration based on `expiresAt`
- **Requirements**: 8.1, 8.3, 10.1, 11.1

**Indexes**:
- `reportId` (unique)
- `userId`
- `queryId`
- `userId + createdAt` (compound)
- `expiresAt` (TTL index with 0 seconds - expires at specified time)

### Alert Rule (`alert.ts`)
- Alert rule definitions and conditions
- Notification channel configurations
- Alert history and acknowledgments
- **Requirements**: 10.1, 10.3, 10.4

**Alert Rule Indexes**:
- `alertRuleId` (unique)
- `userId`
- `userId + enabled` (compound)
- `condition.metric`
- `tags`

**Alert History Indexes**:
- `alertHistoryId` (unique)
- `alertRuleId`
- `userId`
- `userId + timestamp` (compound)
- `timestamp`
- `acknowledged`

### Query History (`query.ts`)
- Query execution history
- Intent classification results
- Conversation context
- Query status tracking
- **Requirements**: 8.1, 8.3, 10.1, 11.1

**Indexes**:
- `queryId` (unique)
- `userId`
- `sessionId`
- `userId + timestamp` (compound)
- `status`
- `intent.type`
- `timestamp`

## Usage

### Initialize Collections

```typescript
import { connectMongoDB } from '../database/mongodb';
import { initializeCollections } from '../models';

const db = await connectMongoDB();
// Collections and indexes are automatically created
```

### Get Typed Collections

```typescript
import { getMongoDB } from '../database/mongodb';
import { getCollections } from '../models';

const db = getMongoDB();
const collections = getCollections(db);

// Use typed collections
const user = await collections.users.findOne({ userId: 'user123' });
const dashboards = await collections.dashboards.find({ userId: 'user123' }).toArray();
```

### Working with Models

```typescript
import { UserProfile, Dashboard, ReportDocument } from '../models';

// Create a new user
const newUser: UserProfile = {
  userId: 'user123',
  email: 'user@example.com',
  expertiseLevel: 'intermediate',
  preferences: {
    defaultTimeRange: { start: '-7d', end: 'now' },
    favoriteMetrics: ['price', 'volume'],
    notificationSettings: {
      email: true,
      webhook: false,
      inApp: true,
      sms: false,
    },
  },
  dashboardIds: [],
  apiKeys: [],
  createdAt: new Date(),
  updatedAt: new Date(),
};

await collections.users.insertOne(newUser);
```

## Schema Design Principles

1. **Denormalization**: Related data is embedded when it's frequently accessed together
2. **Indexing**: Indexes are created for all common query patterns
3. **TTL Indexes**: Automatic cleanup of expired documents (reports)
4. **Compound Indexes**: Optimize queries that filter by multiple fields
5. **Sparse Indexes**: Only index documents that have the field (e.g., API keys)

## Data Retention

- **Reports**: Automatically deleted based on `expiresAt` field (TTL index)
- **Query History**: Retained indefinitely (consider adding TTL in future)
- **Alert History**: Retained indefinitely (consider archiving old alerts)
- **User Data**: Retained until user deletion

## Performance Considerations

- Use projection to limit returned fields
- Leverage indexes for all queries
- Use aggregation pipeline for complex queries
- Consider read preferences for scaling (primary/secondary reads)
- Monitor slow queries and add indexes as needed
