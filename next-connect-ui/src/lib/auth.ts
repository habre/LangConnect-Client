import { NextAuthOptions } from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"
import { serverFetchAPI } from "./api"

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      id: "credentials",
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
        type: { label: "Type", type: "string" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null
        }

        try {
          const response = await serverFetchAPI(credentials.type === 'signup' ? '/auth/signup' : '/auth/signin', {
            method: "POST",
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password
            })
          })
          
          const user = {
            id: response.user_id,
            email: response.email,
            name: response.name,
            accessToken: response.access_token,
          }
          
          return user as any
        } catch (error: any) {
          // 이메일 확인이 필요한 경우를 처리
          if (credentials.type === 'signup' && error?.detail?.includes('check your email')) {
            throw new Error('EMAIL_VERIFICATION_REQUIRED')
          }
          // 사용자가 이미 존재하는 경우
          if (error?.detail?.includes('User already exists')) {
            throw new Error('USER_ALREADY_EXISTS')
          }
          return null
        }
      }
    })
  ],
  callbacks: {
    async jwt({ token, user }) {
      // user is only available on sign in
      if (user) {
        token.accessToken = user.accessToken
        token.id = user.id
        token.email = user.email
        token.name = user.name
      }
      
      return token
    },
    async session({ session, token }) {
      if (token && session.user) {
        session.user.id = token.id as string
        session.user.email = token.email as string
        session.user.name = token.name as string
        session.user.accessToken = token.accessToken as string
      }
      
      return session
    }
  },
  pages: {
    signIn: "/signin",
    error: "/error",
    newUser: "/signup",
  },
  session: {
    strategy: "jwt",
    maxAge: 24 * 60 * 60, // 24 hours
  },
  events: {
    async signOut(message) {
      // 로그아웃 시 추가 정리 작업
    }
  },
  secret: process.env.NEXTAUTH_SECRET,
}
