---
title: "Phase 7: UI Components"
priority: P2
status: pending
effort: 2h
---

# Phase 7: UI Components (Login + Protected Routes)

## Context

- **Link to Plan:** [plan.md](plan.md)
- **Phase 6:** [phase-06-environment-config.md](phase-06-environment-config.md)

## Overview

Create login page with OAuth2 buttons and protected route wrappers.

## Key Insights

- Login page with Google/GitHub buttons
- Protected route HOC pattern
- User profile dropdown with role display

## Requirements

### Functional
- Login page with OAuth2 buttons
- Protected route wrappers
- User profile dropdown
- Role-based UI elements

### Non-functional
- Responsive design
- Accessible (WCAG 2.1 AA)
- Loading states

## Architecture

```
Component Tree:
App
├── PublicRoute (redirect if authenticated)
│   └── LoginPage
│       ├── GoogleLoginButton
│       └── GitHubLoginButton
├── ProtectedRoute (redirect if not authenticated)
│   ├── Dashboard
│   ├── AdminPanel (admin+ only)
│   └── Settings
└── Layout
    └── UserProfileDropdown
        ├── Role badge
        └── Logout button
```

## Implementation Steps

1. **Create login page** `src/ui/pages/login_page.tsx`
   ```tsx
   import { Button } from "@/components/ui/button";

   export function LoginPage() {
     return (
       <div className="min-h-screen flex items-center justify-center bg-gray-50">
         <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
           <h1 className="text-3xl font-bold text-center">Sign In</h1>
           <p className="text-center text-gray-600">
             Choose your preferred login method
           </p>

           <div className="space-y-4">
             <a href="/auth/google">
               <Button className="w-full" variant="outline">
                 <GoogleIcon className="mr-2 h-5 w-5" />
                 Continue with Google
               </Button>
             </a>

             <a href="/auth/github">
               <Button className="w-full" variant="outline">
                 <GitHubIcon className="mr-2 h-5 w-5" />
                 Continue with GitHub
               </Button>
             </a>
           </div>
         </div>
       </div>
     );
   }
   ```

2. **Create protected route wrapper** `src/ui/components/protected-route.tsx`
   ```tsx
   import { Navigate, useLocation } from "react-router-dom";
   import { useAuth } from "@/hooks/use-auth";

   interface ProtectedRouteProps {
     children: React.ReactNode;
     requiredRole?: "owner" | "admin" | "member" | "viewer";
   }

   export function ProtectedRoute({
     children,
     requiredRole = "viewer",
   }: ProtectedRouteProps) {
     const { user, loading } = useAuth();
     const location = useLocation();

     if (loading) {
       return <LoadingSpinner />;
     }

     if (!user) {
       return <Navigate to="/login" state={{ from: location }} replace />;
     }

     const roleHierarchy = {
       viewer: 0,
       member: 1,
       admin: 2,
       owner: 3,
     };

     if (roleHierarchy[user.role] < roleHierarchy[requiredRole]) {
       return <Navigate to="/unauthorized" replace />;
     }

     return <>{children}</>;
   }
   ```

3. **Create user profile dropdown** `src/ui/components/user-profile-dropdown.tsx`
   ```tsx
   import {
     DropdownMenu,
     DropdownMenuContent,
     DropdownMenuItem,
     DropdownMenuSeparator,
     DropdownMenuTrigger,
   } from "@/components/ui/dropdown-menu";
   import { useAuth } from "@/hooks/use-auth";

   export function UserProfileDropdown() {
     const { user, logout } = useAuth();

     return (
       <DropdownMenu>
         <DropdownMenuTrigger>
           <Avatar>
             <AvatarImage src={user?.avatar} />
             <AvatarFallback>{user?.email[0]}</AvatarFallback>
           </Avatar>
         </DropdownMenuTrigger>
         <DropdownMenuContent align="end">
           <div className="p-2">
             <p className="text-sm font-medium">{user?.email}</p>
             <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
           </div>
           <DropdownMenuSeparator />
           <DropdownMenuItem>
             <a href="/profile">Profile</a>
           </DropdownMenuItem>
           <DropdownMenuItem>
             <a href="/settings">Settings</a>
           </DropdownMenuItem>
           {user?.role === "owner" && (
             <>
               <DropdownMenuSeparator />
               <DropdownMenuItem>
                 <a href="/admin">Admin Panel</a>
               </DropdownMenuItem>
             </>
           )}
           <DropdownMenuSeparator />
           <DropdownMenuItem onClick={logout}>
             Sign out
           </DropdownMenuItem>
         </DropdownMenuContent>
       </DropdownMenu>
     );
   }
   ```

4. **Create auth hook** `src/hooks/use-auth.ts`
   ```tsx
   import { useState, useEffect } from "react";

   interface User {
     id: string;
     email: string;
     role: "owner" | "admin" | "member" | "viewer";
     avatar?: string;
   }

   export function useAuth() {
     const [user, setUser] = useState<User | null>(null);
     const [loading, setLoading] = useState(true);

     useEffect(() => {
       fetch("/api/auth/me")
         .then((res) => res.json())
         .then((data) => {
           setUser(data.user);
           setLoading(false);
         })
         .catch(() => {
           setLoading(false);
         });
     }, []);

     const logout = async () => {
       await fetch("/api/auth/logout", { method: "POST" });
       setUser(null);
       window.location.href = "/";
     };

     return { user, loading, logout };
   }
   ```

## Todo List

- [ ] Create `src/ui/pages/login_page.tsx`
- [ ] Create `src/ui/components/protected-route.tsx`
- [ ] Create `src/ui/components/user-profile-dropdown.tsx`
- [ ] Create `src/hooks/use-auth.ts`
- [ ] Update router with protected routes

## Success Criteria

- [ ] Login page renders with both OAuth buttons
- [ ] Protected routes redirect to login
- [ ] Profile dropdown shows user info
- [ ] Logout works correctly

## Next Steps

→ Phase 8: Testing
