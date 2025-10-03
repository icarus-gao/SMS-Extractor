import json
from django.core.management.base import BaseCommand
from projects.models import Schema

class Command(BaseCommand):
    help = 'Creates the 6 Research Question (RQ) schemas for the BFT-SMS project.'

    SCHEMAS_DATA = [
        {
            "name": "RQ1 - BFT Protocol Evolution",
            "description": "Extracts information about a protocol's design origins, theoretical underpinnings, and core features.",
            "category": "BFT-SMS",
            "fields": [
                {"field_id": "protocol_name", "name": "Protocol Name", "type": "Text", "description": "The name of the protocol being analyzed (e.g., 'Fast-HotStuff')."},
                {"field_id": "protocol_family", "name": "Protocol Family", "type": "Select", "description": "The lineage it belongs to.", "options": ["PBFT-based", "HotStuff-based", "Tendermint-based", "DAG-based", "Sharding-based", "Other"]},
                {"field_id": "publication_year", "name": "Publication Year", "type": "Number", "description": "Year the paper was published."},
                {"field_id": "theoretical_model", "name": "Theoretical Model", "type": "Select", "description": "The network model assumed.", "options": ["Synchronous", "Asynchronous", "Partial Synchrony", "Dynamic/Permissionless"]},
                {"field_id": "core_crypto_tools", "name": "Core Crypto Tools", "type": "Text Area", "description": "Key cryptographic primitives used (e.g., 'Threshold Signatures', 'Verifiable Delay Functions (VDFs)', 'BLS Signatures')."},
                {"field_id": "key_features", "name": "Key Features", "type": "Text Area", "description": "Bullet points of standout features (e.g., '- Pipelined voting\\n- Optimistic responsiveness\\n- Fast view-change')."},
                {"field_id": "main_contribution", "name": "Main Contribution", "type": "Text Area", "description": "A summary of how this protocol advances the state-of-the-art."}
            ]
        },
        {
            "name": "RQ2 - Security and Robustness",
            "description": "Captures the adversarial model, addressed attacks, and defense mechanisms of a protocol.",
            "category": "BFT-SMS",
            "fields": [
                {"field_id": "adversary_model", "name": "Adversary Model", "type": "Select", "description": "The type of adversary assumed.", "options": ["Static Byzantine", "Adaptive Byzantine", "Rational (Game Theoretic)", "Network-level Attacker"]},
                {"field_id": "fault_assumption", "name": "Fault Assumption", "type": "Text", "description": "The fault tolerance threshold (e.g., 'n=3f+1', 'f < n/2 honest majority')."},
                {"field_id": "attacks_addressed", "name": "Attacks Addressed", "type": "Text Area", "description": "Specific attacks the protocol defends against (e.g., 'DDoS on leader', 'Long-range attacks', 'Equivocation')."},
                {"field_id": "defense_mechanisms", "name": "Defense Mechanisms", "type": "Text Area", "description": "The techniques used to achieve robustness (e.g., 'Reputation system for leader selection', 'Random beacon for unpredictability')."},
                {"field_id": "security_properties", "name": "Claimed Security Properties", "type": "Checkboxes", "description": "The guarantees provided.", "options": ["Safety (Consistency)", "Liveness (Availability)", "Fairness", "Censorship Resistance"]},
                {"field_id": "proof_type", "name": "Proof Type", "type": "Select", "description": "How security is proven.", "options": ["Formal Proof (e.g., TLA+, Coq)", "Informal Argument", "Simulation-based", "Not Specified"]}
            ]
        },
        {
            "name": "RQ3 - Theoretical Performance Limits",
            "description": "Documents the theoretical bounds on communication, latency, and message complexity.",
            "category": "BFT-SMS",
            "fields": [
                {"field_id": "communication_complexity", "name": "Communication Complexity", "type": "Text", "description": "The amount of data exchanged per decision (e.g., 'O(n^2)', 'O(n log n)')."},
                {"field_id": "message_complexity", "name": "Message Complexity", "type": "Number", "description": "The number of messages required per decision."},
                {"field_id": "latency_rounds", "name": "Latency (Rounds)", "type": "Text", "description": "The number of communication rounds to commit a block in the best/worst case (e.g., '2 rounds (optimistic)', '4 rounds (pessimistic)')."},
                {"field_id": "proposer_complexity", "name": "Proposer Complexity", "type": "Text", "description": "The computational work for the leader (e.g., 'O(n)')."},
                {"field_id": "replica_complexity", "name": "Replica Complexity", "type": "Text", "description": "The computational work for a replica (e.g., 'O(1)')."},
                {"field_id": "theoretical_throughput_limit", "name": "Throughput Limit Analysis", "type": "Text Area", "description": "Any discussion on the theoretical maximum throughput."}
            ]
        },
        {
            "name": "RQ4 - Performance and Scalability",
            "description": "Identifies optimization techniques and scalability mechanisms like sharding.",
            "category": "BFT-SMS",
            "fields": [
                {"field_id": "optimization_techniques", "name": "Optimization Techniques", "type": "Text Area", "description": "Methods used to improve performance (e.g., 'Batching transactions', 'Pipelining consensus stages', 'Speculative execution')."},
                {"field_id": "scalability_mechanism", "name": "Scalability Mechanism", "type": "Select", "description": "The primary approach to scaling.", "options": ["Single-Chain Optimization", "Sharding (State/Transaction)", "DAG-based Parallelism", "Sub-committees", "Not Applicable"]},
                {"field_id": "sharding_details", "name": "Sharding Details", "type": "Text Area", "description": "If sharding is used, describe its type, cross-shard communication method, and reconfiguration strategy."},
                {"field_id": "performance_tradeoffs", "name": "Performance Trade-offs", "type": "Text Area", "description": "The trade-offs made (e.g., 'Reduced latency at the cost of higher communication overhead', 'Increased throughput but slower finality')."}
            ]
        },
        {
            "name": "RQ5 - Validation and Evaluation",
            "description": "Collects data on proof methods, experimental platforms, and evaluation metrics to assess credibility and reproducibility.",
            "category": "BFT-SMS",
            "fields": [
                {"field_id": "properties_proven", "name": "Properties Proven", "type": "Text Area", "description": "Which properties were formally or informally proven (e.g., 'Safety under partial synchrony', 'Liveness after GST')."},
                {"field_id": "experimental_platform", "name": "Experimental Platform", "type": "Text", "description": "The software/hardware used for experiments (e.g., 'AWS EC2 t2.medium instances', 'Custom simulator in Go')."},
                {"field_id": "workload_description", "name": "Workload Description", "type": "Text Area", "description": "The type of workload used for testing (e.g., 'Simple key-value store operations', 'Ethereum-like smart contract transactions')."},
                {"field_id": "key_metrics_measured", "name": "Key Metrics Measured", "type": "Checkboxes", "description": "The metrics reported in the evaluation.", "options": ["Throughput (TPS)", "Latency (seconds)", "Communication Overhead (MB/s)", "CPU/Memory Usage"]},
                {"field_id": "comparison_protocols", "name": "Comparison Protocols", "type": "Text", "description": "Which other protocols were used as a baseline for comparison (e.g., 'HotStuff', 'PBFT')."},
                {"field_id": "reproducibility_artifacts", "name": "Reproducibility Artifacts", "type": "Select", "description": "Are artifacts available?", "options": ["Code Repository (e.g., GitHub)", "Container (e.g., Docker)", "Raw Data", "None"]}
            ]
        },
        {
            "name": "RQ6 - Adaptability for Emerging Scenarios",
            "description": "Assesses protocol suitability for resource-constrained and dynamic environments like IoT.",
            "category": "BFT-SMS",
            "fields": [
                {"field_id": "target_scenario", "name": "Target Scenario", "type": "Select", "description": "The primary application context.", "options": ["General Purpose", "IoT", "Fintech/Payments", "Blockchain/Crypto", "Edge Computing"]},
                {"field_id": "network_assumptions", "name": "Network Assumptions", "type": "Text Area", "description": "Assumptions about network topology and stability (e.g., 'Stable, low-churn network', 'Assumes intermittent connectivity')."},
                {"field_id": "resource_constraints", "name": "Resource Constraints Addressed", "type": "Checkboxes", "description": "Which constraints are considered.", "options": ["Low CPU", "Low Memory", "Low Bandwidth", "Low Power"]},
                {"field_id": "design_adaptations", "name": "Design Adaptations", "type": "Text Area", "description": "Specific design changes for the target scenario (e.g., 'Lightweight cryptographic primitives', 'Leaderless design to avoid single point of failure', 'Gossip-based communication')."},
                {"field_id": "dynamic_membership", "name": "Dynamic Membership Support", "type": "Select", "description": "Does the protocol support nodes joining/leaving?", "options": ["Yes (with reconfiguration protocol)", "Yes (permissionless)", "No (static membership)"]}
            ]
        }
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to create RQ schemas...'))

        for schema_data in self.SCHEMAS_DATA:
            schema_name = schema_data['name']
            
            # Check if schema already exists
            if Schema.objects.filter(name=schema_name).exists():
                self.stdout.write(self.style.WARNING(f'Schema "{schema_name}" already exists. Skipping.'))
                continue

            # Create the schema
            try:
                fields_definition = {"fields": schema_data['fields']}
                
                Schema.objects.create(
                    name=schema_name,
                    description=schema_data['description'],
                    category=schema_data['category'],
                    fields_definition=json.dumps(fields_definition, indent=4),
                    created_by='system' # Or use a specific user
                )
                self.stdout.write(self.style.SUCCESS(f'Successfully created schema: "{schema_name}"'))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Error creating schema "{schema_name}": {e}'))

        self.stdout.write(self.style.SUCCESS('All RQ schemas processed.'))
