// SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
// Copyright (C) 2026 Noxfort Systems
//
// File: ui/src_ui/components/settings/tabs/database/useDatabaseSettings.ts
// Author: Gabriel Moraes
// Date: 2026-09-14

import { useState, useEffect } from 'react';
import { systemService } from '../../../../services/api';
import { useSystemStore } from '../../../../stores';

export const DB_STORAGE_KEY = 'synapse_database_settings_v1';

export const getSavedDbSettings = () => {
  try {
    const raw = localStorage.getItem(DB_STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch (e) {
    console.error('Error loading db settings from localStorage:', e);
  }
  return null;
};

export function useDatabaseSettings() {
  const saved = getSavedDbSettings();
  const { setDbStatus } = useSystemStore();

  const [dbHost, setDbHost] = useState(saved?.host ?? 'localhost');
  const [dbPort, setDbPort] = useState(saved?.port ?? 5432);
  const [dbName, setDbName] = useState(saved?.dbname ?? '');
  const [dbSchema, setDbSchema] = useState(saved?.schema ?? 'schema_synapse');
  const [dbUser, setDbUser] = useState(saved?.user ?? '');
  const [dbPass, setDbPass] = useState(saved?.password ?? '');
  const [dbRootPass, setDbRootPass] = useState('');
  const [dbFeedback, setDbFeedback] = useState<{ ok: boolean; msg: string } | null>(null);
  const [dbLoading, setDbLoading] = useState(false);
  const [isConnected, setIsConnected] = useState<boolean>(saved?.connected ?? false);
  const [isSetupDone, setIsSetupDone] = useState<boolean>(saved?.setupDone ?? false);

  // Load persistent settings directly from backend settings.ini on mount
  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const backendCfg = await systemService.getDatabaseConfig();
        if (mounted && backendCfg) {
          if (backendCfg.host) setDbHost(backendCfg.host);
          if (backendCfg.port) setDbPort(backendCfg.port);
          if (backendCfg.dbname) setDbName(backendCfg.dbname);
          if (backendCfg.schema) setDbSchema(backendCfg.schema);
          if (backendCfg.user) setDbUser(backendCfg.user);
          if (backendCfg.password) setDbPass(backendCfg.password);
          if (typeof backendCfg.connected === 'boolean') {
            setIsConnected(backendCfg.connected);
            if (backendCfg.connected) {
              setDbStatus({
                connected: true,
                message: `Conectado ao schema '${backendCfg.schema || 'schema_synapse'}'`,
              });
            } else {
              setDbStatus({ connected: false, message: 'Desconectado' });
            }
          }
          if (typeof backendCfg.setup_done === 'boolean') {
            setIsSetupDone(backendCfg.setup_done);
          }
        }
      } catch (e) {
        console.warn('Could not load database settings from backend:', e);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [setDbStatus]);

  // Auto-persist settings to localStorage on any modification
  useEffect(() => {
    try {
      localStorage.setItem(
        DB_STORAGE_KEY,
        JSON.stringify({
          host: dbHost,
          port: dbPort,
          dbname: dbName,
          schema: dbSchema,
          user: dbUser,
          password: dbPass,
          connected: isConnected,
          setupDone: isSetupDone,
        })
      );
    } catch (e) {
      console.error('Error saving db settings to localStorage:', e);
    }
  }, [dbHost, dbPort, dbName, dbSchema, dbUser, dbPass, isConnected, isSetupDone]);

  const handleFieldChange = (setter: (val: any) => void) => (val: any) => {
    setter(val);
    setIsConnected(false);
    setIsSetupDone(false);
    setDbFeedback(null);
    setDbStatus({ connected: false, message: 'Configurações alteradas' });
  };

  const handleConnect = async () => {
    setDbLoading(true);
    setDbFeedback(null);
    try {
      const res = await systemService.testDbConnection({
        host: dbHost,
        port: Number(dbPort),
        dbname: dbName,
        schema: dbSchema,
        user: dbUser,
        password: dbPass,
      });
      setIsConnected(true);
      setDbStatus({ connected: true, message: `Conectado ao schema '${dbSchema}'` });
      setDbFeedback({
        ok: true,
        msg: res?.message || 'Conexão estabelecida com sucesso ao banco PostgreSQL!',
      });
    } catch (err: any) {
      setIsConnected(false);
      setDbStatus({ connected: false, message: err?.message || 'Falha na conexão' });
      setDbFeedback({ ok: false, msg: err?.message || 'Falha ao conectar no PostgreSQL.' });
    } finally {
      setDbLoading(false);
    }
  };

  const handleDisconnect = async () => {
    setIsConnected(false);
    setDbStatus({ connected: false, message: 'Desconectado pelo usuário' });
    setDbFeedback({ ok: true, msg: 'Desconectado do banco de dados com sucesso.' });
    try {
      await systemService.disconnectDb();
    } catch {}
  };

  const handleInitializeDb = async () => {
    setDbLoading(true);
    setDbFeedback(null);
    try {
      const res = await systemService.initializeDb(dbRootPass, {
        host: dbHost,
        port: Number(dbPort),
        dbname: dbName,
        schema: dbSchema,
        user: dbUser,
        password: dbPass,
      });
      setIsSetupDone(true);
      setIsConnected(true);
      setDbStatus({ connected: true, message: `Schema '${dbSchema}' provisionado e ativo` });
      setDbFeedback({
        ok: true,
        msg: res?.message || 'Estrutura do banco inicializada com sucesso!',
      });
    } catch (err: any) {
      setIsSetupDone(false);
      setDbFeedback({ ok: false, msg: err?.message || 'Erro ao inicializar infraestrutura.' });
    } finally {
      setDbLoading(false);
    }
  };

  return {
    dbHost,
    setDbHost,
    dbPort,
    setDbPort,
    dbName,
    setDbName,
    dbSchema,
    setDbSchema,
    dbUser,
    setDbUser,
    dbPass,
    setDbPass,
    dbRootPass,
    setDbRootPass,
    dbFeedback,
    dbLoading,
    isConnected,
    isSetupDone,
    handleFieldChange,
    handleConnect,
    handleDisconnect,
    handleInitializeDb,
  };
}
