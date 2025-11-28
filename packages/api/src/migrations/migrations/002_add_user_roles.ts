import { Db } from 'mongodb';
import { Migration } from '../types';

/**
 * Add user roles field
 * Example migration showing how to add a new field to existing documents
 */
export const migration002: Migration = {
  version: 2,
  name: 'add_user_roles',
  description: 'Add roles field to user profiles',

  async up(db: Db): Promise<void> {
    // Add roles field to all existing users
    await db.collection('users').updateMany(
      { roles: { $exists: false } },
      { $set: { roles: ['user'] } }
    );

    console.log('Added roles field to user profiles');
  },

  async down(db: Db): Promise<void> {
    // Remove roles field from all users
    await db.collection('users').updateMany(
      {},
      { $unset: { roles: '' } }
    );

    console.log('Removed roles field from user profiles');
  },
};
