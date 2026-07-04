"""Self-custody wallet for USDT on blockchain (Ethereum/Tron)."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional, Tuple

from web3 import Web3
from tronpy import Tron
from tronpy.providers import HTTPProvider

from .config import settings
from .exceptions import SelfCustodyError, InsufficientFundsError

logger = logging.getLogger(__name__)

# USDT contract addresses
USDT_CONTRACTS = {
    "ethereum": "0xdac17f958d2ee523a2206206994597c13d831ec7",  # Mainnet
    "sepolia": "0x7169c345e4f8c4c4a80e86a4f6362f45e6c6d88a",  # Testnet
    "tron": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",  # TRC20 USDT
}

# ERC20 ABI (simplified)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_to", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "transfer",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
]


class SelfCustodyWallet:
    """Self-custody wallet for cryptocurrency (USDT)."""

    def __init__(
        self,
        mnemonic: str,
        eth_rpc_url: Optional[str] = None,
        tron_rpc_url: Optional[str] = None,
    ):
        """Initialize self-custody wallet."""
        self.mnemonic = mnemonic
        self.eth_rpc_url = eth_rpc_url or settings.eth_rpc_url
        self.tron_rpc_url = tron_rpc_url or settings.tron_rpc_url

        # Initialize Web3 for Ethereum
        self.w3_eth = None
        self.account_eth = None
        if self.eth_rpc_url:
            self.w3_eth = Web3(Web3.HTTPProvider(self.eth_rpc_url))
            # Derive account from mnemonic (standard derivation path m/44'/60'/0'/0/0)
            try:
                from eth_account import Account
                Account.enable_unaudited_hdwallet_features()
                self.account_eth = Account.from_mnemonic(
                    mnemonic,
                    account_path="m/44'/60'/0'/0/0"
                )
                logger.info(f"Initialized ETH wallet: {self.account_eth.address}")
            except Exception as e:
                logger.error(f"Failed to initialize ETH account: {e}")

        # Initialize Tron client
        self.client_tron = None
        self.account_tron = None
        if self.tron_rpc_url:
            self.client_tron = Tron(HTTPProvider(self.tron_rpc_url))
            # Tron uses same mnemonic derivation
            try:
                from tronpy.keys import PrivateKey
                self.account_tron = Tron.generate_address_from_mnemonic(mnemonic)
                logger.info(f"Initialized TRON wallet: {self.account_tron['base58check_address']}")
            except Exception as e:
                logger.error(f"Failed to initialize TRON account: {e}")

    def get_eth_address(self) -> Optional[str]:
        """Get Ethereum address."""
        if self.account_eth:
            return self.account_eth.address
        return None

    def get_tron_address(self) -> Optional[str]:
        """Get Tron address."""
        if self.account_tron:
            return self.account_tron["base58check_address"]
        return None

    async def get_usdt_balance_eth(self) -> Decimal:
        """Get USDT balance on Ethereum."""
        if not self.w3_eth or not self.account_eth:
            raise SelfCustodyError("Ethereum wallet not initialized")

        try:
            contract = self.w3_eth.eth.contract(
                address=Web3.to_checksum_address(USDT_CONTRACTS["ethereum"]),
                abi=ERC20_ABI
            )
            balance_wei = contract.functions.balanceOf(self.account_eth.address).call()
            decimals = contract.functions.decimals().call()
            balance = Decimal(balance_wei) / Decimal(10 ** decimals)
            return balance
        except Exception as e:
            logger.error(f"Failed to get ETH USDT balance: {e}")
            raise SelfCustodyError(f"Balance check failed: {e}")

    async def get_usdt_balance_tron(self) -> Decimal:
        """Get USDT balance on Tron (TRC20)."""
        if not self.client_tron or not self.account_tron:
            raise SelfCustodyError("Tron wallet not initialized")

        try:
            address = self.account_tron["base58check_address"]
            contract = self.client_tron.get_contract(USDT_CONTRACTS["tron"])
            balance = contract.functions.balanceOf(address).call()
            # TRC20 USDT has 6 decimals
            return Decimal(balance) / Decimal(10 ** 6)
        except Exception as e:
            logger.error(f"Failed to get TRON USDT balance: {e}")
            raise SelfCustodyError(f"Balance check failed: {e}")

    async def send_usdt_eth(
        self,
        to_address: str,
        amount: Decimal,
        gas_limit: Optional[int] = None,
    ) -> Tuple[str, str]:
        """Send USDT on Ethereum network."""
        if not self.w3_eth or not self.account_eth:
            raise SelfCustodyError("Ethereum wallet not initialized")

        try:
            contract = self.w3_eth.eth.contract(
                address=Web3.to_checksum_address(USDT_CONTRACTS["ethereum"]),
                abi=ERC20_ABI
            )

            # Convert amount to token decimals (6 for USDT)
            amount_wei = int(amount * Decimal(10 ** 6))

            # Check balance
            balance = contract.functions.balanceOf(self.account_eth.address).call()
            if balance < amount_wei:
                raise InsufficientFundsError(
                    f"Insufficient USDT balance: {balance / 10**6}, requested: {amount}"
                )

            # Build transaction
            nonce = self.w3_eth.eth.get_transaction_count(self.account_eth.address)
            tx = contract.functions.transfer(
                Web3.to_checksum_address(to_address),
                amount_wei
            ).build_transaction({
                "from": self.account_eth.address,
                "nonce": nonce,
                "gas": gas_limit or 100000,
                "gasPrice": self.w3_eth.eth.gas_price,
            })

            # Sign and send
            signed_tx = self.account_eth.sign_transaction(tx)
            tx_hash = self.w3_eth.eth.send_raw_transaction(signed_tx.rawTransaction)

            logger.info(f"Sent USDT on ETH: {amount} to {to_address}, tx: {tx_hash.hex()}")
            return tx_hash.hex(), "pending"

        except Exception as e:
            logger.error(f"Failed to send USDT on ETH: {e}")
            raise SelfCustodyError(f"Transfer failed: {e}")

    async def send_usdt_tron(
        self,
        to_address: str,
        amount: Decimal,
    ) -> Tuple[str, str]:
        """Send USDT on Tron network (TRC20)."""
        if not self.client_tron or not self.account_tron:
            raise SelfCustodyError("Tron wallet not initialized")

        try:
            contract = self.client_tron.get_contract(USDT_CONTRACTS["tron"])
            from tronpy.keys import PrivateKey

            # Convert amount to sun (TRON has 6 decimals for USDT)
            amount_sun = int(amount * Decimal(10 ** 6))

            # Build and sign transaction
            txn = (
                contract.functions.transfer(to_address, amount_sun)
                .with_owner(self.account_tron["base58check_address"])
                .fee_limit(1_000_000)
                .build()
                .sign(PrivateKey(bytes.fromhex(self.account_tron["private_key"])))
            )

            # Broadcast
            result = txn.broadcast().wait()
            tx_id = txn.txid

            logger.info(f"Sent USDT on TRON: {amount} to {to_address}, tx: {tx_id}")
            return tx_id, "confirmed" if result.get("receipt") else "pending"

        except Exception as e:
            logger.error(f"Failed to send USDT on TRON: {e}")
            raise SelfCustodyError(f"Transfer failed: {e}")

    async def get_transaction_status(
        self,
        tx_hash: str,
        network: str = "ethereum",
    ) -> str:
        """Get transaction status."""
        if network == "ethereum" and self.w3_eth:
            try:
                receipt = self.w3_eth.eth.get_transaction_receipt(tx_hash)
                if receipt:
                    return "confirmed" if receipt.status == 1 else "failed"
                return "pending"
            except Exception:
                return "pending"
        elif network == "tron" and self.client_tron:
            try:
                tx = self.client_tron.get_transaction(tx_hash)
                return "confirmed" if tx.get("ret", [{}])[0].get("contractRet") == "SUCCESS" else "failed"
            except Exception:
                return "pending"

        return "unknown"

    def get_supported_networks(self) -> list[str]:
        """Get list of supported networks."""
        networks = []
        if self.w3_eth and self.account_eth:
            networks.append("ethereum")
        if self.client_tron and self.account_tron:
            networks.append("tron")
        return networks

    @classmethod
    def from_settings(cls) -> Optional[SelfCustodyWallet]:
        """Create wallet from application settings."""
        if not settings.enable_self_custody:
            return None

        if not settings.wallet_mnemonic_encrypted:
            logger.warning("No encrypted mnemonic configured for self-custody wallet")
            return None

        # In production, decrypt the mnemonic using a KMS or environment key
        # For now, we expect plain mnemonic in dev
        mnemonic = settings.wallet_mnemonic_encrypted
        return cls(
            mnemonic=mnemonic,
            eth_rpc_url=settings.eth_rpc_url,
            tron_rpc_url=settings.tron_rpc_url,
        )
