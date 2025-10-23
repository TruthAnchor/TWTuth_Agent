# Advanced Twitter Sentiment & Crypto Pricing Platform

This project is an advanced, modular, and interoperable platform designed to harness real-time Twitter sentiment for predicting cryptocurrency price changes. By integrating a Twitter scraper with AI-driven tweet analysis, decentralized storage on Filecoin, and on-chain data provenance via smart contracts, this project delivers a state-of-the-art solution that addresses modern challenges in data integrity, ethical data sourcing, and efficient AI deployment.

---

## Overview

The platform collects tweets using an advanced scraper, analyzes tweet content using AI agents (powered by LangChain and LangGraph), and combines the resulting sentiment data with historical crypto pricing data to predict coin price movements. The system’s output is archived as CSV files that are stored immutably on Filecoin using Storacha. On-chain smart contracts are used to record dataset metadata, ensuring transparent data provenance and fair attribution.

---

## Key Challenges Addressed

- **Data Provenance:**  
  Filecoin's immutable storage guarantees transparent lineage and verification of data authenticity. On-chain smart contracts (like AIDatasetRegistry) reinforce trust by registering dataset metadata, ensuring that the data used for AI training and market prediction remains untampered.

- **Data Sourcing & Ethics:**  
  The scraper collects high-quality Twitter data while respecting user privacy. With decentralized storage and DAOs, the project facilitates ethical sourcing and proper incentives for authentic contributions.

- **Fair Attribution:**  
  Smart contracts and decentralized data marketplaces enable transparent and fair compensation for data creators. This is crucial in an era of AI-generated content.

- **Efficient AI & Environmental Considerations:**  
  By decentralizing data storage and using advanced AI models with consistent and explainable reasoning (chain-of-thought), our architecture minimizes computational waste and lowers the environmental impact of high-energy computations.

- **Modular Architecture & Interchain Interoperability:**  
  The system is built in a modular fashion, allowing seamless upgrades and integrations across multiple blockchain networks. This open architecture supports agentic economies where autonomous agents interact to optimize resource allocation.

---

## System Architecture

### 1. Twitter Scraper & AI Analysis
- **Scraper Functionality:**  
  Built using Selenium and enhanced by headless browser automation, the scraper collects tweets based on specific queries (e.g., tweets mentioning “ethereum”).  
- **Tweet Analysis:**  
  Each tweet is passed through an AI agent that assesses its “deletion likelihood” (a proxy for controversial sentiment) using LangChain. The analysis is refined via chain-of-thought reasoning and persistent memory techniques for consistent judgment.

### 2. Decentralized Storage with Filecoin
- **CSV Generation & CAR Conversion:**  
  After scraping, tweets are saved into a CSV file. This CSV is then converted into a CAR file using IPFS tools.
- **Storacha Integration:**  
  The CAR file is uploaded to Filecoin through Storacha, ensuring that every dataset has a verifiable and immutable record.

### 3. Crypto Pricing Model
- **Historical & Sentiment Data:**  
  The enriched tweet dataset (with sentiment scores) is combined with historical market data to feed a predictive pricing model.
- **Prediction & Trading Insight:**  
  The model leverages aggregated social sentiment to forecast future price movements, providing vital insights for market analysis and trading strategies.

### 4. On-Chain Data Provenance & Governance
- **Smart Contracts:**  
  - **AIDatasetRegistry:** Registers dataset metadata (title, CID, file size, description, price, Filecoin deal ID, preview) on-chain.  
    _Deployed at:_ `0x8fa300Faf24b9B764B0D7934D8861219Db0626e5`
    
  - **DatasetAccessAgent:** Allows users to request and gain access to datasets by paying a fee, with AI agents listening to emitted events for further processing.  
    _Deployed at:_ `0xf0f994B4A8dB86A46a1eD4F12263c795b26703Ca`
    
  - **TruthToken:** A utility token that incentivizes data contributions and facilitates fair compensation.  
    _Deployed at:_ `0x959e85561b3cc2E2AE9e9764f55499525E350f56`
    
  - **MyTimelockController:** Manages secure, time-locked transactions and operations on-chain.  
    _Deployed at:_ `0x62FD5Ab8b5b1d11D0902Fce5B937C856301e7bf8`
    
  - **TruthAnchorGovernor:** Implements decentralized governance, enabling proposals (e.g., candidate Twitter handles) and voting based on collected sentiment data.  
    _Deployed at:_ `0x5F8E67E37e223c571D184fe3CF4e27cae33E81fF`

---

## Installation & Setup

### Prerequisites
- **Python 3.8+**
- **Node.js & npm** (for some auxiliary tools)
- **IPFS & ipfs-car CLI Tools** (ensure they are installed and available in your PATH)
- A properly configured **.env** file containing:
  ```ini
  TWITTER_MAIL=your_twitter_mail
  TWITTER_USERNAME=your_twitter_username
  TWITTER_PASSWORD=your_twitter_password
  HEADLESS=yes
  PINATA_API_KEY=your_pinata_api_key
  PINATA_API_SECRET=your_pinata_api_secret
  PINATA_JWT=your_pinata_jwt
  W3UP_SPACE_DID=your_space_did
  W3UP_XAUTH=your_xauth
  W3UP_AUTH=your_authorization_token
  OPEN_AI_API_KEY=your_openai_api_key


## Improving Consistency of Judgment
- **Calibrate the System Prompt:**  
  Refine the agent's prompt to include clear guidelines and examples on what constitutes controversial content.
- **Chain-of-Thought Reasoning:**  
  Update the prompt to require a brief reasoning summary (chain-of-thought) before providing the final controversy score.
- **Memory Integration:**  
  Utilize persistent memory (e.g., `ConversationBufferMemory`) to store previous analyses for consistent decisions over time.
- **Consistency Checker Subchain:**  
  Implement a subchain that cross-checks the deletion likelihood score with additional tools (e.g., sentiment analysis) to validate results.

## Advanced LangGraph Integration
- **Interactive Visualization:**  
  Leverage LangGraph's visualization API to create interactive graphs of the agent’s reasoning process.
- **Graph-Based Workflow:**  
  Break down the tweet analysis into modular nodes (e.g., content extraction, sentiment evaluation, controversy assessment) and edges that show the data flow.
- **Utilize Prebuilt Agents:**  
  Integrate LangGraph prebuilt agents (such as a ReAct agent) for multi-step reasoning and tool usage.
- **Graph Debugging Hooks:**  
  Add logging and hooks at key decision points to generate visual summaries of the chain, aiding in debugging and improvement.



# Future Roadmap
| Deliverable                                      | Implementation                                                                                                                                                                                                                                     |
|--------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Refine AI agents and LLM flow                    | Improve the controversy detection agent and introduce multimodal sentiment scoring using Hugging Face models such as `ProsusAI/finbert` and `cardiffnlp/twitter-roberta-base-sentiment`, potentially including fine-tuning on crypto-specific data |
| Expand coin/ecosystem sentiment feeds            | Scale scraping to support all major coins and ecosystems; add an LLM agent to classify tweets by ecosystem or token; integrate broader on- and off-chain pricing APIs for richer analysis                                                         |
| Voting flow → agent trigger integration          | Modify backend to distinguish between proposals to follow users vs. scrape ecosystems; use LLM agents to determine intent and trigger appropriate scraping logic                                                                                   |
| Frontend integrations + analytics dashboards     | Finalize frontend integrations with voting contract, Filecoin, and IPFS; implement dashboards for viewing storage deals and tweet sentiment analytics                                                                                              |
| Data cleaning + Filecoin archiving               | Add a post-run data cleaning agent and integrate its output with the Filecoin deal creation pipeline via AIDatasetRegistry                                                                                                                        |
| Autonomous scheduling via governance             | Build mechanism for on-chain governance votes to auto-schedule new scraping runs or follow accounts                                                                                                                                                |
| Backend hosted deployment                        | Deploy the scraping and analysis backend in a cloud environment (e.g., AWS) for continuous, reliable execution                                                                                                                                    |
| User-initiated scraping jobs                     | Enable users to start scraping jobs via auxiliary Twitter accounts by interacting with a backend submission and scheduling interface                                                                                                               |



MAINNET CONTRACTS:
IP_DEPOSIT_CONTRACT_MAINNET=0x06Aa51D53e9a2218a934B5614B4D83AAEd694fFd
TWEET_REGISTRY_CONTRACT=0x4CefBd73390F4738D2b94083dcE951745538e28B


Testing:
Mainnet txn immutable tweet submission test:
 python tweet_submitter.py \
  --url "https://x.com/Ashcryptoreal/status/1977255774788444420" \
  --score 0.85 \
  --force

Test all blockchain integrations:
python main_daemon.py --once