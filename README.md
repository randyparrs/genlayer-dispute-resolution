# GenLayer Dispute Resolution

An onchain dispute resolution contract built on GenLayer where two parties submit their side of a conflict and an AI arbitrator decides who has the stronger case.

## What is this

I built this as part of the GenLayer Bradbury Hackathon. The idea came from thinking about how hard it is to resolve disputes fairly when there is no neutral third party. With GenLayer, the AI acts as that neutral party and multiple validators have to agree on the outcome before anything gets committed onchain.

The interesting part is that the AI does not just flip a coin. It actually reads both sides of the story and makes a judgment based on the evidence. When I tested it with a freelancer payment conflict, the result changed depending on which party submitted stronger evidence.

## How it works

Someone opens a dispute by providing a title, the names of both parties, and some background context about the situation. Then each party submits their evidence explaining their side. Once both sides have been heard, anyone can call resolve and the AI evaluates everything and picks a winner.

Multiple validators on the GenLayer network independently read the same evidence and have to agree on who wins before the result is final. This is the Optimistic Democracy consensus in action.

## Example

I tested it with this scenario:

A client hired a freelancer to build a website. The freelancer delivered the work but the client refused to pay claiming the quality was poor.

When only the client submitted evidence the AI ruled in favor of the client with 100 percent confidence since there was nothing to counter the claims. When the freelancer also submitted evidence explaining they had approval messages and the client kept changing requirements, the AI ruled in favor of the freelancer with 80 percent confidence.

This shows the contract actually weighs the evidence rather than just picking a side.

## Functions

open_dispute takes a title, the names of both parties, and context about the situation

submit_evidence takes the dispute id, the party (A or B), and the evidence text

resolve takes the dispute id and triggers the AI evaluation

get_dispute shows the current status, winner, confidence, and reasoning

get_summary shows how many total disputes have been created

## How to run it

Go to GenLayer Studio at https://studio.genlayer.com and create a new file called dispute_resolution.py. Paste the contract code and set the execution mode to Normal Full Consensus. Deploy with your address as owner_address.

Then follow this order. Open a dispute first and wait for it to finalize. Check get_dispute to confirm the status says open before submitting any evidence. Submit evidence for Party A and wait for it to finalize. Then submit evidence for Party B and wait again. Only call resolve after both evidences are finalized.

Note: the contract in this repository uses the Address type in the constructor as required by genvm-lint. When deploying in GenLayer Studio use a version that receives str in the constructor and converts internally with Address(owner_address) since Studio requires primitive types to parse the contract schema correctly.

## Built with

GenLayer Studio, Python using the GenLayer Intelligent Contract SDK, gl.vm.run_nondet_unsafe for the Equivalence Principle, and Optimistic Democracy consensus.

## Notes

This was built for the Bradbury Special Track of the GenLayer Hackathon focusing on Subjective Consensus. The contract demonstrates how AI validators can resolve real world disputes that require judgment rather than just deterministic computation.
