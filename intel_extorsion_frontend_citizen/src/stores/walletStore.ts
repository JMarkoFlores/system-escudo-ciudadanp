import { create } from 'zustand';

interface WalletState {
  account: string | null;
  chainId: number | null;
  isConnected: boolean;
  provider: any | null;
  did: string | null;
  reputation: number;
  error: string | null;
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  switchToZkSYS: () => Promise<void>;
  setDID: (did: string) => void;
  init: () => void;
}

const ZKSYS_CHAIN_ID = 57057;
const ZKSYS_HEX = '0xdf01';
const EXPLORER_URL = 'https://explorer-zk.tanenbaum.io';

function formatDID(address: string): string {
  return `did:zsys:tanenbaum:${address.toLowerCase()}`;
}

export const useWalletStore = create<WalletState>((set, get) => ({
  account: null,
  chainId: null,
  isConnected: false,
  provider: null,
  did: null,
  reputation: 0,
  error: null,

  init: () => {
    if (typeof window === 'undefined') return;
    const pali = (window as any).pali || (window as any).ethereum;
    if (!pali) return;

    // Solo configurar si no se ha configurado antes
    if (get().provider && get().provider === pali) return;

    const handleAccountsChanged = (accounts: string[]) => {
      if (accounts.length === 0) {
        get().disconnect();
      } else {
        set({
          account: accounts[0],
          did: formatDID(accounts[0]),
        });
      }
    };

    const handleChainChanged = (chainIdHex: string) => {
      const chainId = parseInt(chainIdHex, 16);
      set({
        chainId,
        error: chainId !== ZKSYS_CHAIN_ID ? 'Por favor cambia a la red zkSYS Tanenbaum Testnet (Chain ID 57057)' : null,
      });
    };

    // Registrar oyentes
    if (pali.on) {
      pali.on('accountsChanged', handleAccountsChanged);
      pali.on('chainChanged', handleChainChanged);
    }

    // Intentar auto-conectar si ya está autorizado
    pali.request({ method: 'eth_accounts' }).then((accounts: string[]) => {
      if (accounts && accounts.length > 0) {
        set({
          account: accounts[0],
          provider: pali,
          isConnected: true,
          did: formatDID(accounts[0]),
        });
        pali.request({ method: 'eth_chainId' }).then((chainIdHex: string) => {
          const chainId = parseInt(chainIdHex, 16);
          set({
            chainId,
            error: chainId !== ZKSYS_CHAIN_ID ? 'Por favor cambia a la red zkSYS Tanenbaum Testnet (Chain ID 57057)' : null,
          });
        });
      }
    }).catch(() => {});

    set({ provider: pali });
  },

  connect: async () => {
    if (typeof window === 'undefined') return;
    const pali = (window as any).pali || (window as any).ethereum;
    if (!pali) {
      set({ error: 'Pali Wallet no detectada. Instálala desde https://paliwallet.com' });
      return;
    }
    try {
      const accounts = await pali.request({ method: 'eth_requestAccounts' });
      const chainIdHex = await pali.request({ method: 'eth_chainId' });
      const chainId = parseInt(chainIdHex, 16);

      set({
        account: accounts[0],
        chainId,
        provider: pali,
        isConnected: true,
        error: chainId !== ZKSYS_CHAIN_ID ? 'Por favor cambia a la red zkSYS Tanenbaum Testnet (Chain ID 57057)' : null,
      });

      // Auto-resolve DID
      const did = formatDID(accounts[0]);
      set({ did });

      // Inicializar listeners si no se han iniciado
      get().init();
    } catch (err: any) {
      set({ error: err.message || 'Error al conectar' });
    }
  },

  disconnect: async () => {
    if (typeof window !== 'undefined') {
      const pali = (window as any).pali || (window as any).ethereum;
      if (pali) {
        try {
          await pali.request({ method: 'wallet_revokePermissions', params: [{ eth_accounts: {} }] });
        } catch {}
      }
    }
    set({
      account: null,
      chainId: null,
      isConnected: false,
      provider: null,
      did: null,
      reputation: 0,
      error: null,
    });
  },

  switchToZkSYS: async () => {
    if (typeof window === 'undefined') return;
    const pali = (window as any).pali || (window as any).ethereum;
    if (!pali) return;
    try {
      await pali.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: ZKSYS_HEX }],
      });
    } catch (switchError: any) {
      if (switchError.code === 4902) {
        await pali.request({
          method: 'wallet_addEthereumChain',
          params: [
            {
              chainId: ZKSYS_HEX,
              chainName: 'zkSYS Tanenbaum Testnet',
              nativeCurrency: { name: 'Syscoin', symbol: 'TSYS', decimals: 18 },
              rpcUrls: ['https://rpc-zk.tanenbaum.io'],
              blockExplorerUrls: ['https://explorer-zk.tanenbaum.io'],
            },
          ],
        });
      }
    }
  },

  setDID: (did: string) => set({ did }),
}));
