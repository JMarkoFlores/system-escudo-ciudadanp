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
  disconnect: () => void;
  switchToRollux: () => Promise<void>;
  setDID: (did: string) => void;
}

const ROLLUX_CHAIN_ID = 570;
const ROLLUX_HEX = '0x23a';

export const useWalletStore = create<WalletState>((set, get) => ({
  account: null,
  chainId: null,
  isConnected: false,
  provider: null,
  did: null,
  reputation: 0,
  error: null,

  connect: async () => {
    const pali = (window as any).pali;
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
        error: chainId !== ROLLUX_CHAIN_ID ? 'Por favor cambia a la red Syscoin Rollux (Chain ID 570)' : null,
      });

      // Auto-resolve DID
      const did = `did:ethr:rollux:${accounts[0]}`;
      set({ did });
    } catch (err: any) {
      set({ error: err.message || 'Error al conectar' });
    }
  },

  disconnect: () => {
    set({
      account: null,
      chainId: null,
      provider: null,
      isConnected: false,
      did: null,
      reputation: 0,
      error: null,
    });
  },

  switchToRollux: async () => {
    const pali = (window as any).pali;
    if (!pali) return;
    try {
      await pali.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: ROLLUX_HEX }],
      });
    } catch (switchError: any) {
      if (switchError.code === 4902) {
        await pali.request({
          method: 'wallet_addEthereumChain',
          params: [
            {
              chainId: ROLLUX_HEX,
              chainName: 'Syscoin Rollux Mainnet',
              nativeCurrency: { name: 'Syscoin', symbol: 'SYS', decimals: 18 },
              rpcUrls: ['https://rpc.rollux.com'],
              blockExplorerUrls: ['https://explorer.rollux.com'],
            },
          ],
        });
      }
    }
  },

  setDID: (did: string) => set({ did }),
}));
