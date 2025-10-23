"use client"

import { useState } from "react"
import { ethers } from "ethers"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Loader2, AlertCircle, CheckCircle2, ExternalLink } from "lucide-react"
import { useTomoWallet } from "@/contexts/tomo-wallet-context"
import { useFallbackWallet } from "@/contexts/fallback-wallet-context"
import { useTwitterConnection } from "@/hooks/use-twitter-connection"
import { getNewIPDepositContract } from "@/lib/contracts"
import { formatTweetUrl, extractTweetId } from "@/lib/utils"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { StylizedButton } from "@/components/ui/stylized-button"

export function SimpleTweetRegistration() {
  const tomoWallet = useTomoWallet()
  const fallbackWallet = useFallbackWallet()
  const { isConnected: isTwitterConnected, handle } = useTwitterConnection()

  const wallet = tomoWallet.isConnected ? tomoWallet : fallbackWallet
  const isWalletConnected = wallet.isConnected
  const address = wallet.address

  const [tweetUrl, setTweetUrl] = useState("")
  const [depositAmount, setDepositAmount] = useState("0.1")
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [txHash, setTxHash] = useState<string | null>(null)

  const handleSubmit = async () => {
    // Strict checks at the beginning
    if (!isWalletConnected || !address || !ethers.isAddress(address)) {
      setError("Please connect a valid wallet using the sidebar.")
      return
    }
    if (!isTwitterConnected || !handle) {
      setError("Please connect your Twitter account using the sidebar.")
      return
    }
    if (!tweetUrl) {
      setError("Please enter a tweet URL.")
      return
    }
    const depositValue = parseFloat(depositAmount);
    if (isNaN(depositValue) || depositValue <= 0) {
        setError("Please enter a valid deposit amount greater than 0.")
        return;
    }


    setIsLoading(true)
    setError(null)
    setSuccess(null)
    setTxHash(null)

    let signer: ethers.Signer | null = null;
    let currentAddress: string | null = null;
    let ipContract: ethers.Contract | null = null;

    try {
      console.log("Starting simple tweet registration...")

      // 1. Get Signer & Validate Address
      if (tomoWallet.isConnected) {
        if (!window.ethereum) throw new Error("Tomo wallet provider (window.ethereum) not found.")
        const provider = new ethers.BrowserProvider(window.ethereum)
        signer = await provider.getSigner()
      } else if (fallbackWallet.signer) {
        signer = fallbackWallet.signer
      } else {
        throw new Error("No available wallet signer.")
      }
      currentAddress = await signer.getAddress();
      if (!ethers.isAddress(currentAddress)) {
         throw new Error("Could not retrieve a valid signer address.")
      }
      console.log("Signer obtained, address:", currentAddress);

      // 2. Prepare Basic Params & Contract
      const tweetId = extractTweetId(tweetUrl)
      if (!tweetId) {
        throw new Error("Invalid tweet URL format. Could not extract tweet ID.")
      }
      const formattedTweetUrl = formatTweetUrl(tweetUrl) // Use consistent URL
      const tweetHash = ethers.keccak256(ethers.toUtf8Bytes(formattedTweetUrl))
      const proof = ethers.toUtf8Bytes(formattedTweetUrl) // Proof is just the URL bytes for simple validation

      ipContract = getNewIPDepositContract(signer) // Get contract with the signer
      console.log("Contract instance created for:", ipContract.target);

      // 3. Prepare Struct Parameters (Using Defaults)
      const recipient = currentAddress;
      const validation = "twitter-verification";
      const collectionAddress = ethers.ZeroAddress;

      // Ensure all BigInts are correctly formatted
      const collectionConfig = {
        handle: handle,
        mintPrice: ethers.parseEther("0.01"), // 0.01 FIL default mint price
        maxSupply: BigInt(100),
        royaltyReceiver: currentAddress,
        royaltyBP: BigInt(500), // 5% = 500 basis points
      };

      const licenseTermsConfig = {
        defaultMintingFee: BigInt(0),
        currency: ethers.ZeroAddress, // Native token (FIL)
        royaltyPolicy: "0xBe54FB168b3c982b7AaE60dB6CF75Bd8447b390E", // Verify this address exists on Filecoin
        transferable: true,
        expiration: BigInt(0),
        commercialUse: true,
        commercialAttribution: true,
        commercialRevShare: BigInt(20), // Default 20%
        commercialRevCeiling: BigInt(0),
        derivativesAllowed: true,
        derivativesAttribution: true,
        derivativesApproval: false,
        derivativesReciprocal: true,
        derivativeRevCeiling: BigInt(0),
        uri: "",
      };

      const licenseMintParams = {
        licenseTermsId: BigInt(1), // Assuming ID 1 exists for these terms
        licensorIpId: ethers.ZeroAddress,
        receiver: currentAddress,
        amount: BigInt(1),
        maxMintingFee: BigInt(0),
        maxRevenueShare: BigInt(100), // Default 100%
      };

      const coCreators: any[] = []; // Empty for simple registration

      // 4. Log Everything Before Sending
       const depositAmountWei = ethers.parseEther(depositAmount)
      console.log("Final Parameters for depositIP call:", JSON.stringify({
          recipient,
          validation,
          proof: ethers.hexlify(proof), // Show bytes as hex string
          collectionAddress,
          collectionConfig: {
              handle: collectionConfig.handle,
              mintPrice: collectionConfig.mintPrice.toString(),
              maxSupply: collectionConfig.maxSupply.toString(),
              royaltyReceiver: collectionConfig.royaltyReceiver,
              royaltyBP: collectionConfig.royaltyBP.toString(), // Ensure BigInt becomes string
          },
          tweetHash,
          licenseTermsConfig: {
              ...licenseTermsConfig,
              defaultMintingFee: licenseTermsConfig.defaultMintingFee.toString(),
              expiration: licenseTermsConfig.expiration.toString(),
              commercialRevShare: licenseTermsConfig.commercialRevShare.toString(),
              commercialRevCeiling: licenseTermsConfig.commercialRevCeiling.toString(),
              derivativeRevCeiling: licenseTermsConfig.derivativeRevCeiling.toString(),
          },
          licenseMintParams: {
               ...licenseMintParams,
               licenseTermsId: licenseMintParams.licenseTermsId.toString(),
               amount: licenseMintParams.amount.toString(),
               maxMintingFee: licenseMintParams.maxMintingFee.toString(),
               maxRevenueShare: licenseMintParams.maxRevenueShare.toString(),
          },
          coCreators,
          value: depositAmountWei.toString(), // Wei value being sent
      }, (key, value) => // Custom replacer for BigInt logging
          typeof value === 'bigint' ? value.toString() : value, 2));


      // 5. Estimate Gas (Keep this uncommented)
      console.log("Estimating gas...");
      let estimatedGas: bigint;
      try {
          // --- Make sure parameters here EXACTLY match the final call ---
          estimatedGas = await ipContract.depositIP.estimateGas(
              recipient, validation, proof, collectionAddress, collectionConfig,
              tweetHash, licenseTermsConfig, licenseMintParams, coCreators,
              { value: depositAmountWei }
          );
          console.log("Estimated Gas:", estimatedGas.toString());
      } catch (estimateError: any) {
          console.error("Gas estimation failed:", estimateError);
          let reason = estimateError.reason || "Reason not provided"; // Ethers v6+
          // Attempt to get more info if available (less common now with estimateError.reason)
          if (estimateError.data) {
              try {
                  const decodedError = ipContract.interface.parseError(estimateError.data);
                  reason = `${decodedError?.name}(${decodedError?.args.join(', ') || ''})` || reason;
                  console.error("Decoded revert data:", decodedError);
              } catch (decodeErr) {
                  console.error("Could not decode revert reason data.");
              }
          }
           console.error(`Revert Reason (from estimateGas): ${reason}`)
           throw new Error(`Gas estimation failed: ${reason}`); // Throw with specific reason
      }

      // 6. Send Transaction
      console.log("Sending transaction with value:", depositAmount, "FIL");
      const tx = await ipContract.depositIP(
        recipient,
        validation,
        proof,
        collectionAddress,
        collectionConfig,
        tweetHash,
        licenseTermsConfig,
        licenseMintParams,
        coCreators,
        {
          value: depositAmountWei,
          // You could potentially add the estimated gas here, but usually not needed
          // gasLimit: estimatedGas ? estimatedGas + BigInt(20000) : undefined // Add buffer
        },
      );

      console.log("Transaction sent, hash:", tx.hash);
      setTxHash(tx.hash);

      console.log("Waiting for transaction confirmation...");
      const receipt = await tx.wait();
      console.log("Transaction confirmed:", receipt);

      if (receipt?.status === 1) {
          setSuccess("Tweet successfully registered as IP!");
      } else {
           throw new Error("Transaction failed after being mined. Check explorer for details.");
      }

    } catch (err: any) {
      console.error("Error during registration:", err);
      let errorMessage = "Failed to register tweet. Check console for details.";
      if (err.code === "ACTION_REJECTED") {
        errorMessage = "Transaction was rejected in wallet.";
      } else if (err.code === "INSUFFICIENT_FUNDS") {
        errorMessage = "Insufficient FIL for deposit + gas fees.";
      } else if (err.message?.includes("Gas estimation failed")) {
           errorMessage = err.message; // Use the specific reason from estimateGas
      } else if (err.message?.includes("Already deposited")) {
           errorMessage = "This tweet has already been registered.";
      } else if (err.reason) { // Catch reverts from the actual transaction send
           errorMessage = `Transaction failed: ${err.reason}`;
      } else if (err.message) {
           errorMessage = err.message;
      }
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }

  // --- Rest of the component (JSX) remains the same ---
  // Ensure labels say "FIL" and explorer link points to Filfox

  const isReady = isWalletConnected && isTwitterConnected;

  return (
    <Card className="border-accent/20">
      <CardHeader>
        <CardTitle>Quick Tweet Registration</CardTitle>
        <CardDescription>Register your tweet as IP with default settings</CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {!isReady && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Connection Required</AlertTitle>
            <AlertDescription>Please connect both your wallet and Twitter account to register tweets.</AlertDescription>
          </Alert>
        )}

        <div className="space-y-2">
          <label htmlFor="tweet-url" className="text-sm font-medium">
            Tweet URL
          </label>
          <Input
            id="tweet-url"
            placeholder="https://twitter.com/username/status/123456789"
            value={tweetUrl}
            onChange={(e) => setTweetUrl(e.target.value)}
            className="border-border/30 focus:border-primary/30 bg-background/30"
            disabled={!isReady}
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="deposit-amount" className="text-sm font-medium">
            Deposit Amount (FIL)
          </label>
          <Input
            id="deposit-amount"
            type="number"
            step="0.01"
            min="0.01"
            placeholder="0.1"
            value={depositAmount}
            onChange={(e) => setDepositAmount(e.target.value)}
            className="border-border/30 focus:border-primary/30 bg-background/30"
            disabled={!isReady}
          />
           <p className="text-xs text-muted-foreground">Amount of FIL to send with the registration.</p>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription className="break-words">{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert variant="default" className="bg-accent/10 border-accent/30">
            <CheckCircle2 className="h-4 w-4" />
            <AlertTitle>Success</AlertTitle>
            <AlertDescription>{success}</AlertDescription>
          </Alert>
        )}

        {txHash && (
          <div className="bg-background/30 border border-border/30 rounded-md p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium">Transaction Hash</h3>
              <a
                href={`https://filfox.info/en/message/${txHash}`} // Using Filfox explorer
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center text-xs text-primary hover:text-primary/80"
              >
                View on Filfox <ExternalLink className="h-3 w-3 ml-1" />
              </a>
            </div>
            <p className="text-xs font-mono break-all">{txHash}</p>
          </div>
        )}

        {isLoading ? (
          <button
            disabled
            className="w-full h-10 px-4 bg-background/80 border border-primary/20 text-muted-foreground rounded-md flex items-center justify-center gap-2"
          >
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Processing...</span>
          </button>
        ) : (
          <StylizedButton
            variant="glow"
            onClick={handleSubmit}
            disabled={!isReady || !tweetUrl || parseFloat(depositAmount) <= 0} // Disable if amount is invalid
            iconRight={<CheckCircle2 className="w-4 h-4" />}
            withIcon={true}
            className="w-full"
          >
            Register IP ({depositAmount} FIL)
          </StylizedButton>
        )}
      </CardContent>
    </Card>
  )
}