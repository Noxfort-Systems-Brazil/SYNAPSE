// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { ITransportClient, getTransportClient, UnlistenFn } from '../transport';

export interface AuthResponse {
  success: boolean;
  role: 'OPERATOR' | 'SUPERUSER' | 'MASTER';
  username: string;
}

export interface UserAccount {
  username: string;
  role: 'OPERATOR' | 'SUPERUSER';
}

export class SecurityService {
  constructor(private transport: ITransportClient = getTransportClient()) {}

  /**
   * Authenticates user credentials against the security manager.
   */
  async authenticate(username: string, password: string): Promise<AuthResponse> {
    return await this.transport.invoke<
      { username: string; password: string },
      AuthResponse
    >('authenticate', { username, password });
  }

  /**
   * Checks if the system is currently in lockdown failsafe mode.
   */
  async checkLockdown(): Promise<{ active: boolean }> {
    return await this.transport.invoke<undefined, { active: boolean }>('check_lockdown');
  }

  /**
   * Lists all registered user accounts.
   */
  async listUsers(): Promise<{ users: UserAccount[] }> {
    return await this.transport.invoke<undefined, { users: UserAccount[] }>('list_users');
  }

  /**
   * Adds a new user account.
   */
  async addUser(username: string, password: string, role: 'OPERATOR' | 'SUPERUSER'): Promise<{ success: boolean; users: UserAccount[] }> {
    return await this.transport.invoke<
      { username: string; password: string; role: string },
      { success: boolean; users: UserAccount[] }
    >('add_user', { username, password, role });
  }

  /**
   * Removes an existing user account (admin is protected).
   */
  async removeUser(username: string): Promise<{ success: boolean; users: UserAccount[] }> {
    return await this.transport.invoke<
      { username: string },
      { success: boolean; users: UserAccount[] }
    >('remove_user', { username });
  }

  /**
   * Fetches the recent security audit logs.
   */
  async getAuditLogs(limit: number = 100): Promise<{ logs: any[] }> {
    return await this.transport.invoke<{ limit: number }, { logs: any[] }>('get_audit_logs', { limit });
  }

  /**
   * Subscribes to backend lockdown events.
   */
  async onLockdownEvent(callback: (data: { active: boolean }) => void): Promise<UnlistenFn> {
    return await this.transport.listen<{ active: boolean }>('synapse:lockdown_event', callback);
  }
}

export const securityService = new SecurityService();
