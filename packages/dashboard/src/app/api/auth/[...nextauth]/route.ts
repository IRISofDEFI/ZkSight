// src/app/api/auth/[...nextauth]/route.ts

import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import Google from "next-auth/providers/google";
import GitHub from "next-auth/providers/github";
import type { NextAuthOptions } from "next-auth";   // ← correct type
import type { JWT } from "next-auth/jwt";           // ← for jwt callback
import type { Session } from "next-auth";           // ← for session callback

// ──────────────────────────────────────────────────────────────
// In-memory fake DB (only for dev/demo)
// ──────────────────────────────────────────────────────────────
interface User {
  id: string;
  email: string;
  password: string;
  name: string;
}

declare global {
  var users: User[] | undefined;
}

if (!global.users) {
  global.users = [
    { id: "1", email: "test@example.com", password: "password123", name: "Test User" },
    { id: "2", email: "admin@chimera.com", password: "admin123", name: "Chimera Admin" },
  ];
}

// ──────────────────────────────────────────────────────────────
// NextAuth config (fully typed)
// ──────────────────────────────────────────────────────────────
const authOptions: NextAuthOptions = {
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    GitHub({
      clientId: process.env.GITHUB_ID!,
      clientSecret: process.env.GITHUB_SECRET!,
    }),
    Credentials({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
        name: { label: "Name", type: "text" },
        action: { label: "Action", type: "text" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) return null;

        const users = global.users!;

        const existingUser = users.find(u => u.email === credentials.email);

        // ────── SIGNUP ──────
        if (credentials.action === "signup") {
          if (existingUser) return null; // email already taken

          const newUser: User = {
            id: String(users.length + 1),
            email: credentials.email,
            password: credentials.password, // NEVER do this in production!
            name: (credentials.name as string) || credentials.email.split("@")[0],
          };

          users.push(newUser);
          return { id: newUser.id, email: newUser.email, name: newUser.name };
        }

        // ────── LOGIN ──────
        if (!existingUser || existingUser.password !== credentials.password) {
          return null;
        }

        return { id: existingUser.id, email: existingUser.email, name: existingUser.name };
      },
    }),
  ],

  pages: {
    signIn: "/login",
  },

  session: {
    strategy: "jwt",
  },

  callbacks: {
    async jwt({ token, user }: { token: JWT; user?: any }) {
      if (user) {
        token.id = user.id as string;
        token.name = user.name;
      }
      return token;
    },

    async session({ session, token }: { session: Session; token: JWT }) {
      if (token.id) {
        session.user.id = token.id as string;
        session.user.name = token.name ?? session.user.name;
      }
      return session;
    },
  },

  debug: process.env.NODE_ENV === "development",
};

// ──────────────────────────────────────────────────────────────
const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };