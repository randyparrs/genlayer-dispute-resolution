# { "Depends": "py-genlayer:test" }

import json
from genlayer import *


class DisputeResolution(gl.Contract):

    owner: Address
    dispute_counter: u256
    dispute_data: DynArray[str]  # flat key:value storage

    def __init__(self, owner_address: Address):
        self.owner = owner_address
        self.dispute_counter = u256(0)

    @gl.public.view
    def get_dispute(self, dispute_id: str) -> str:
        title = self._get(dispute_id, "title")
        if not title:
            return "Dispute not found"
        return (
            f"ID: {dispute_id} | "
            f"Title: {title} | "
            f"Status: {self._get(dispute_id, 'status')} | "
            f"Winner: {self._get(dispute_id, 'winner')} | "
            f"Confidence: {self._get(dispute_id, 'confidence')}% | "
            f"Reasoning: {self._get(dispute_id, 'reasoning')}"
        )

    @gl.public.view
    def get_dispute_count(self) -> u256:
        return self.dispute_counter

    @gl.public.view
    def get_summary(self) -> str:
        return (
            f"Onchain Dispute Resolution\n"
            f"Total Disputes: {int(self.dispute_counter)}"
        )

    @gl.public.write
    def open_dispute(
        self,
        title: str,
        party_a_name: str,
        party_b_name: str,
        context: str,
    ) -> str:
        caller = str(gl.message.sender_address)
        dispute_id = str(int(self.dispute_counter))

        self._set(dispute_id, "title", title)
        self._set(dispute_id, "opener", caller)
        self._set(dispute_id, "party_a", party_a_name)
        self._set(dispute_id, "party_b", party_b_name)
        self._set(dispute_id, "context", context[:500])
        self._set(dispute_id, "evidence_a", "")
        self._set(dispute_id, "evidence_b", "")
        self._set(dispute_id, "status", "open")
        self._set(dispute_id, "winner", "")
        self._set(dispute_id, "confidence", "0")
        self._set(dispute_id, "reasoning", "")

        self.dispute_counter = u256(int(self.dispute_counter) + 1)
        return f"Dispute {dispute_id} opened. Title: {title}"

    @gl.public.write
    def submit_evidence(
        self,
        dispute_id: str,
        party: str,
        evidence: str,
    ) -> str:
        assert self._get(dispute_id, "status") == "open", "Dispute is not open"
        assert party in ("A", "B"), "Party must be A or B"
        assert 10 <= len(evidence) <= 1000, "Evidence must be 10 to 1000 characters"

        field = "evidence_a" if party == "A" else "evidence_b"
        self._set(dispute_id, field, evidence[:1000])

        party_name = self._get(dispute_id, f"party_{party.lower()}")
        return f"Evidence submitted for {party_name} in dispute {dispute_id}"

    @gl.public.write
    def resolve(self, dispute_id: str) -> str:
        assert self._get(dispute_id, "status") == "open", "Dispute is not open"

        title = self._get(dispute_id, "title")
        context = self._get(dispute_id, "context")
        party_a = self._get(dispute_id, "party_a")
        party_b = self._get(dispute_id, "party_b")
        evidence_a = self._get(dispute_id, "evidence_a")
        evidence_b = self._get(dispute_id, "evidence_b")

        assert evidence_a or evidence_b, "At least one party must submit evidence"

        if not evidence_a:
            evidence_a = "No evidence submitted by this party"
        if not evidence_b:
            evidence_b = "No evidence submitted by this party"

        def leader_fn():
            prompt = f"""You are an impartial arbitrator resolving a dispute between two parties.
Read both sides carefully and decide who has the stronger case.

Dispute title: {title}

Background context:
{context}

Evidence from {party_a}:
{evidence_a}

Evidence from {party_b}:
{evidence_b}

Based on the evidence provided, decide who has the stronger case.
If one party did not submit evidence, rule in favor of the party that did.

Respond only with this JSON format:
{{"winner": "A", "confidence": 80, "reasoning": "two sentences explaining the decision"}}

Where winner is exactly A or B, confidence is an integer from 0 to 100,
and reasoning is two sentences maximum based only on the evidence provided.
No extra text."""

            result = gl.nondet.exec_prompt(prompt)
            clean = result.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)

            winner = data.get("winner", "A")
            confidence = int(data.get("confidence", 50))
            reasoning = data.get("reasoning", "")

            if winner not in ("A", "B"):
                winner = "A"
            confidence = max(0, min(100, confidence))

            return json.dumps({
                "winner": winner,
                "confidence": confidence,
                "reasoning": reasoning
            }, sort_keys=True)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                validator_raw = leader_fn()
                leader_data = json.loads(leader_result.calldata)
                validator_data = json.loads(validator_raw)
                if leader_data["winner"] != validator_data["winner"]:
                    return False
                return abs(leader_data["confidence"] - validator_data["confidence"]) <= 10
            except Exception:
                return False

        raw = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        data = json.loads(raw)

        winner_label = data["winner"]
        confidence = data["confidence"]
        reasoning = data["reasoning"]

        if winner_label == "A":
            winner_name = self._get(dispute_id, "party_a")
        else:
            winner_name = self._get(dispute_id, "party_b")

        self._set(dispute_id, "status", "resolved")
        self._set(dispute_id, "winner", winner_name)
        self._set(dispute_id, "confidence", str(confidence))
        self._set(dispute_id, "reasoning", reasoning)

        return (
            f"Dispute {dispute_id} resolved. "
            f"Winner: {winner_name} ({confidence}% confidence). "
            f"{reasoning}"
        )

    def _get(self, dispute_id: str, field: str) -> str:
        key = f"{dispute_id}_{field}:"
        for i in range(len(self.dispute_data)):
            if self.dispute_data[i].startswith(key):
                return self.dispute_data[i][len(key):]
        return ""

    def _set(self, dispute_id: str, field: str, value: str) -> None:
        key = f"{dispute_id}_{field}:"
        for i in range(len(self.dispute_data)):
            if self.dispute_data[i].startswith(key):
                self.dispute_data[i] = f"{key}{value}"
                return
        self.dispute_data.append(f"{key}{value}")
 
       
