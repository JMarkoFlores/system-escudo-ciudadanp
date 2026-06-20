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
  switchToZkSYS: () => Promise<void>;
  setDID: (did: string) => void;
}

const ZKSYS_CHAIN_ID = 5700;
const ZKSYS_HEX = '0x1644';

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
        error: chainId !== ZKSYS_CHAIN_ID ? 'Por favor cambia a la red zkSYS Genesis Testnet (Chain ID 5700)' : null,
      });

      // Auto-resolve DID
      const did = `did:zksys:${accounts[0]}`;
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

  switchToZkSYS: async () => {
    const pali = (window as any).pali;
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
              chainName: 'zkSYS Genesis Testnet',
              nativeCurrency: { name: 'Syscoin', symbol: 'SYS', decimals: 18 },
              rpcUrls: ['https://rpc.genesis.zksys.io'],
              blockExplorerUrls: ['https://explorer.genesis.zksys.io'],
            },
          ],
        });
      }
    }
  },

  setDID: (did: string) => set({ did }),
}));
