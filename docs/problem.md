# Real-World Problem & Security Need

## 1. The Real-World Student Challenge
Students face a fragmented, manual, and error-prone scholarship application workflow:
- Searching across dozens of central and state government portals.
- Manually reading eligibility criteria and calculating income limits.
- Preparing state domicile, income certificates, and marksheet documents.
- Filling redundant application forms.
- Tracking application status across multiple sites.

While AI agents can automate this workflow, **unrestricted AI autonomy creates a critical security risk**.

## 2. The Core Security Problem
When a student instructs an AI agent:
> *"Find government scholarships I am eligible for in Punjab and apply to them."*

During execution, an autonomous agent may reason:
> *"Applying to this high-value private scholarship will maximize student funding."*

Or:
> *"Modifying the income certificate value slightly will qualify the student for an additional grant."*

The fundamental question is: **Did the student actually authorize that action?**

AI agents can reason freely, but **they cannot manufacture authority**. Without an enforceable connection between user intent and tool execution, autonomous agents expand their effective authority beyond what was authorized.

## 3. How ArmorIQ Resolves the Authority Problem
ScholarShield integrates **ArmorIQ Intent Engine** directly into the tool execution path.
- **Intent Binding**: User constraints are canonicalized into an execution plan and cryptographically signed.
- **Short-Lived Intent Tokens**: Tools can only be executed if accompanied by a valid, signed ArmorIQ Intent Token matching the registered plan constraints.
- **Fail-Closed Governance**: If an agent attempts an out-of-scope action, ArmorIQ returns a `BLOCK` decision, and the underlying consequential tool is **never executed**.
