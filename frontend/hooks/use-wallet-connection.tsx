"use client"

import { useState, useEffect } from "react"
import { ethers } from "ethers"

declare global {
  interface Window {
    ethereum?: any
  }
}

export function useWalletConnection() {
  const [isConnected, setIsConnected] = useState(false)
  const [address, setAddress] = useState<string | undefined>(undefined)
  const [provider, setProvider] = useState<ethers.BrowserProvider | null>(null)
  const [signer, setSigner] = useState<ethers.JsonRpcSigner | null>(null)

  useEffect(() => {
    // Check if wallet is already connected
    const checkConnection = async () => {
      if (window.ethereum) {
        try {
          const ethersProvider = new ethers.BrowserProvider(window.ethereum)
          const accounts = await ethersProvider.listAccounts()

          if (accounts.length > 0) {
            const ethersSigner = await ethersProvider.getSigner()
            setIsConnected(true)
            setAddress(accounts[0].address)
            setProvider(ethersProvider)
            setSigner(ethersSigner)
          }
        } catch (error) {
          console.error("Error checking wallet connection:", error)
        }
      }
    }

    checkConnection()

    // Listen for account changes
    if (window.ethereum) {
      window.ethereum.on("accountsChanged", (accounts: string[]) => {
        if (accounts.length > 0) {
          setIsConnected(true)
          setAddress(accounts[0])
        } else {
          setIsConnected(false)
          setAddress(undefined)
          setSigner(null)
        }
      })
    }

    return () => {
      if (window.ethereum) {
        window.ethereum.removeAllListeners("accountsChanged")
      }
    }
  }, [])

  const connect = async () => {
    if (window.ethereum) {
      try {
        const ethersProvider = new ethers.BrowserProvider(window.ethereum)
        await ethersProvider.send("eth_requestAccounts", [])
        const accounts = await ethersProvider.listAccounts()

        if (accounts.length > 0) {
          const ethersSigner = await ethersProvider.getSigner()
          setIsConnected(true)
          setAddress(accounts[0].address)
          setProvider(ethersProvider)
          setSigner(ethersSigner)
        }
      } catch (error) {
        console.error("Error connecting wallet:", error)
      }
    } else {
      alert("Please install a Web3 wallet like MetaMask")
    }
  }

  const disconnect = () => {
    setIsConnected(false)
    setAddress(undefined)
    setProvider(null)
    setSigner(null)
  }

  return {
    isConnected,
    address,
    provider,
    signer,
    connect,
    disconnect,
  }
}
