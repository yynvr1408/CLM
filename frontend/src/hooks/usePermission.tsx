/**
 * Permission hooks and guard components for RBAC
 */
import React from 'react';
import { useSelector } from 'react-redux';
import { RootState } from '../store';

/**
 * Check if current user has a specific permission
 */
export const usePermission = (permission: string): boolean => {
  const user = useSelector((state: RootState) => state.auth.user);
  if (!user) return false;
  if (user.is_superuser) return true;
  return user.permissions?.includes(permission) ?? false;
};

/**
 * Check if current user has ANY of the given permissions
 */
export const useAnyPermission = (...permissions: string[]): boolean => {
  const user = useSelector((state: RootState) => state.auth.user);
  if (!user) return false;
  if (user.is_superuser) return true;
  return permissions.some(p => user.permissions?.includes(p));
};

/**
 * Check if current user has ALL of the given permissions
 */
export const useAllPermissions = (...permissions: string[]): boolean => {
  const user = useSelector((state: RootState) => state.auth.user);
  if (!user) return false;
  if (user.is_superuser) return true;
  return permissions.every(p => user.permissions?.includes(p));
};

/**
 * Get current user's role name
 */
export const useRoleName = (): string => {
  const user = useSelector((state: RootState) => state.auth.user);
  return user?.role_name || 'unknown';
};

/**
 * Guard component that renders children only if user has the required permission
 */
export const PermissionGuard: React.FC<{
  permission: string;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}> = ({ permission, fallback = null, children }) => {
  const hasPermission = usePermission(permission);
  return hasPermission ? <>{children}</> : <>{fallback}</>;
};

/**
 * Guard component that renders children if user has ANY of the permissions
 */
export const AnyPermissionGuard: React.FC<{
  permissions: string[];
  fallback?: React.ReactNode;
  children: React.ReactNode;
}> = ({ permissions, fallback = null, children }) => {
  const hasPermission = useAnyPermission(...permissions);
  return hasPermission ? <>{children}</> : <>{fallback}</>;
};
