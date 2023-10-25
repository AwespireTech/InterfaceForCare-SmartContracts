import smartpy as sp

MetadataUrl = "ipfs://bafkreib3tcjga2piffydhk3bb773qpikqcjdaip3ibpdlmlgokusodwj4u"

DefaultBaker = "tz1V16tR1LMKRernkmXzngkfznmEcTGXwDuk"
TokenFA2 = sp.address("KT1QxN1rKscZuEWE3xsABXNeurZMyoBkDYGc")
TokenMetadataGenerator = sp.address("KT1F5TgdEDUWH64d8ubFGosi45zbX5uhxrbc")
PayloadGenerator = sp.address("KT1EwMY7edPs6L1JNkEAyTU5qVSwZfVkYi5i")

Admin = sp.address("tz1UikAq5Po4wefKL4WkzAHqmCDVnUC1AKAS")


approve_type = sp.TSet(sp.TAddress)

transfer_tez_type = sp.TRecord(
    to_ = sp.TAddress,
    amount = sp.TMutez
)

update_agreement_uri_type = sp.TBytes

update_dataset_uri_type = sp.TBytes

update_threshold_type = sp.TRecord(
    ratio_number = sp.TNat,
    ratio_total = sp.TNat,
    minimum_count = sp.TNat
)

update_generation_duration_minute_type = sp.TInt

update_metadata_type = sp.TRecord(
    key = sp.TString,
    value = sp.TBytes
)

lambda_ops_type = sp.TLambda(
    sp.TUnit,
    sp.TList(sp.TOperation)
)

proposal_content_type = sp.TVariant(
    transfer_tez = transfer_tez_type,
    update_agreement_uri = update_agreement_uri_type,
    update_dataset_uri = update_dataset_uri_type,
    update_threshold = update_threshold_type,
    update_generation_duration_minute = update_generation_duration_minute_type,
    update_metadata = update_metadata_type,
    lambda_ops = lambda_ops_type
)

t_balance_of_request = sp.TRecord(owner=sp.TAddress, token_id=sp.TNat).layout(
    ("owner", "token_id")
)

t_balance_of_response = sp.TRecord(
    request=t_balance_of_request, balance=sp.TNat
).layout(("request", "balance"))

proposal_value_type = sp.TRecord(
    approved = approve_type,
    is_resolved = sp.TBool,
    proposer = sp.TAddress,
    create_time = sp.TTimestamp,
    generation = sp.TNat,
    content = proposal_content_type
)

event_value_type = sp.TRecord(
    approved = approve_type,
    passed = sp.TBool,
    proposer = sp.TAddress,
    create_time = sp.TTimestamp,
    generation = sp.TNat,
    token_id = sp.TNat,
    amount = sp.TOption(sp.TNat),
    claims = sp.TMap(sp.TAddress, sp.TSignature)
)


class MultiSigFactory(sp.Contract):
    def __init__(self, addresses):
        self.multi_sig = MultiSig()
        self.init(
            addresses = addresses,
            duration_minute = sp.record(
                gen0 = sp.int(30*60*24),
                genX = sp.int(90*60*24)
            ),
            default_threshold = sp.record(
                ratio_number = 1,
                ratio_total = 3,
                minimum_count = 20
            ),
            baker = sp.some(sp.key_hash(DefaultBaker)),
            multisigs = sp.big_map(
                tkey = sp.TAddress,
                tvalue = sp.TRecord(
                    creator = sp.TAddress,
                    name = sp.TBytes,
                    create_time = sp.TTimestamp
                )
            ),
            metadata = sp.big_map({"":sp.utils.bytes_of_string(MetadataUrl)})
        )

    def is_admin(self):
        sp.verify(sp.sender == self.data.addresses["admin"], "NOT_ADMIN")
        
    def zero_tez(self):
        sp.verify(sp.amount == sp.tez(0), "TEZOS_NOT_ACCEPTED")
    
    @sp.entry_point
    def default(self):
        sp.send(sp.sender, sp.amount)

    @sp.entry_point
    def create_multisig(self, name, description, agreement_uri, dataset_uri, contract_metadata):
        self.zero_tez()
        sp.set_type(name, sp.TBytes)
        sp.set_type(description, sp.TBytes)
        sp.set_type(agreement_uri, sp.TBytes)
        sp.set_type(dataset_uri, sp.TBytes)
        sp.set_type(contract_metadata, sp.TBytes)

        # create multisig
        contract_address = sp.create_contract(
            storage = sp.record(
                info = sp.record(
                    name = name,
                    description = description,
                    generation = sp.nat(0),
                    generation_duration_minute = self.data.duration_minute.genX
                ),
                addresses = sp.record(
                    factory = sp.self_address,
                    token_metadata_generator = self.data.addresses["token_metadata_generator"],
                    payload_generator = self.data.addresses["payload_generator"]
                ),
                timestamp = sp.record(
                    create_time = sp.now,
                    generation_start_time = sp.now,
                    generation_end_time = sp.now.add_minutes(self.data.duration_minute.gen0)
                ),
                event = sp.record(
                    event_token_fa2 = self.data.addresses["event_token_fa2"],
                    next_event_id = sp.nat(0),
                    event_id_list = sp.list([]),
                    events = sp.big_map(
                        tkey = sp.TNat,
                        tvalue = event_value_type,
                        l = {}
                    )
                ),
                proposal = sp.record(
                    next_proposal_id = sp.nat(0),
                    proposals = sp.big_map(
                        tkey = sp.TNat,
                        tvalue = proposal_value_type,
                        l = {}
                    )
                ),
                agreement_uri = agreement_uri,
                dataset_uri = dataset_uri,
                gen0_stewardship_signatures = sp.big_map(
                    tkey = sp.TAddress,
                    tvalue = sp.TSignature,
                    l = {}
                ),
                stewardship_token = sp.record(
                    fa2 = self.data.addresses["stewardship_token_fa2"],
                    id = sp.nat(0)
                ),
                threshold = self.data.default_threshold,
                metadata = sp.big_map(l = {"": contract_metadata})
            ),
            contract = self.multi_sig, 
            amount = sp.tez(0),
            baker = self.data.baker
        )
        
        # create stewardship token
        c_self_create = sp.self_entrypoint("_create_gen0_token")
        sp.transfer(contract_address, sp.mutez(0), c_self_create)
        
        # record multisig info
        self.data.multisigs[contract_address] = sp.record(
            creator = sp.sender,
            name = name,
            create_time = sp.now
        )

    @sp.entry_point
    def _create_gen0_token(self, multisig_address):
        sp.verify(sp.sender == sp.self_address, "ONLY_SELF_CALL")
        c_create = sp.contract(
            sp.TUnit, 
            multisig_address, 
            entry_point = "create_gen0_stewardship").open_some()
        
        sp.transfer(
            sp.unit, 
            sp.mutez(0), 
            c_create
        )
    
    @sp.entry_point
    def _update_address(self, name, address):
        self.is_admin()
        self.data.addresses[name] = address

    @sp.entry_point
    def _update_duration(self, duration_minute):
        self.is_admin()
        self.data.duration_minute = duration_minute

    @sp.entry_point
    def _update_default_threshold(self, default_threshold):
        self.is_admin()
        self.data.default_threshold = default_threshold

    @sp.entry_point
    def _update_baker(self, baker):
        self.is_admin()
        self.data.baker = baker

    @sp.entry_point
    def _update_metadata(self, key, value):
        self.is_admin()
        self.data.metadata[key] = value

    @sp.entry_point
    def _remove_multisig(self, address):
        self.is_admin()
        del self.data.multisigs[address]

    
    
    @sp.onchain_view()
    def is_multisig(self, params):
        sp.result(self.data.multisigs.contains(params))
    





class MultiSig(sp.Contract):
    def __init__(self):
        self.init(
            info = sp.record(
                name = sp.utils.bytes_of_string("River"),
                description = sp.utils.bytes_of_string("This is a river."),
                generation = sp.nat(0),
                generation_duration_minute = sp.int(129600)
            ),
            addresses = sp.record(
                factory = TokenFA2,
                token_metadata_generator = TokenMetadataGenerator,
                payload_generator = PayloadGenerator
            ),
            timestamp = sp.record(
                create_time = sp.timestamp(0),
                generation_start_time = sp.timestamp(0),
                generation_end_time = sp.timestamp(0)
            ),
            event = sp.record(
                event_token_fa2 = TokenFA2,
                next_event_id = sp.nat(0),
                event_id_list = sp.list([]),
                events = sp.big_map(
                    tkey = sp.TNat,
                    tvalue = event_value_type
                )
            ),
            proposal = sp.record(
                next_proposal_id = sp.nat(0),
                proposals = sp.big_map(
                    tkey = sp.TNat,
                    tvalue = proposal_value_type
                )
            ),
            agreement_uri = sp.utils.bytes_of_string(MetadataUrl),
            dataset_uri = sp.utils.bytes_of_string(MetadataUrl),
            gen0_stewardship_signatures = sp.big_map(
                tkey = sp.TAddress,
                tvalue = sp.TSignature
            ),
            stewardship_token = sp.record(
                fa2 = TokenFA2,
                id = sp.nat(0)
            ),
            threshold = sp.record(
                ratio_number = 1,
                ratio_total = 3,
                minimum_count = 20
            ),
            metadata = sp.big_map({"":sp.utils.bytes_of_string(MetadataUrl)})
        )
    
    @sp.entry_point
    def default(self):
        pass

    def zero_tez(self):
        sp.verify(sp.amount == sp.tez(0), "TEZOS_NOT_ACCEPTED")
    
    def check_member(self, address):
        balanceResult = sp.view("get_balance_of", self.data.stewardship_token.fa2, sp.list([sp.record(owner=address, token_id=self.data.stewardship_token.id)]), sp.TList(t_balance_of_response)).open_some("open get_balance_of view Error")
        sp.for balanceData in balanceResult:
            sp.verify(balanceData.balance > 0, "NO_OWNING_STEWARDSHIP_TOKEN")

    def check_valid_time(self):
        sp.verify(sp.now < self.data.timestamp.generation_end_time, "OVER_GENERATION_END_TIME")
        sp.verify(self.data.info.generation > 0, "NOT_ACTIVATED_YET")

    def check_threshold(self, approveCount):
        st_holders = sp.view("get_token_holders", self.data.stewardship_token.fa2, self.data.stewardship_token.id, sp.TSet(sp.TAddress)).open_some("open get_token_holders view Error")
        return (approveCount >= self.data.threshold.minimum_count) & (approveCount * self.data.threshold.ratio_total >= sp.len(st_holders) * self.data.threshold.ratio_number)


    def validate_proposal(self, content):
        with content.match_cases() as arg:
            with arg.match("transfer_tez") as proposal_data:
                sp.verify(proposal_data.amount > sp.tez(0), "CANNOT_SEND_ZERO_TEZ")
            with arg.match("update_agreement_uri") as proposal_data:
                pass
            with arg.match("update_dataset_uri") as proposal_data:
                pass
            with arg.match("update_threshold") as proposal_data:
                st_holders = sp.view("get_token_holders", self.data.stewardship_token.fa2, self.data.stewardship_token.id, sp.TSet(sp.TAddress)).open_some("open get_token_holders view Error")
                holderCount = sp.compute(sp.len(st_holders))
                sp.verify(proposal_data.minimum_count <= holderCount, "MINIMUM_COUNT_ERROR: over holders count")
                sp.verify(proposal_data.ratio_number <= proposal_data.ratio_total, "RATIO_ERROR: numerator should not greater than denominator")
            with arg.match("update_generation_duration_minute") as proposal_data:
                pass
            with arg.match("update_metadata") as proposal_data:
                pass
            with arg.match("lambda_ops") as proposal_data:
                pass

    
    def execute_transfer_tez(self, content, proposal_id):
        sp.send(content.to_, content.amount)
        self.data.proposal.proposals[proposal_id].is_resolved = True
        
    def execute_update_agreement_uri(self, content, proposal_id):
        self.data.agreement_uri = content
        self.data.proposal.proposals[proposal_id].is_resolved = True
        
    def execute_update_dataset_uri(self, content, proposal_id):
        self.data.dataset_uri = content
        self.data.proposal.proposals[proposal_id].is_resolved = True

    def execute_update_threshold(self, content, proposal_id):
        self.data.threshold = content
        self.data.proposal.proposals[proposal_id].is_resolved = True

    def execute_update_generation_duration_minute(self, content, proposal_id):
        self.data.info.generation_duration_minute = content
        self.data.proposal.proposals[proposal_id].is_resolved = True

    def execute_update_metadata(self, content, proposal_id):
        self.data.metadata[content.key] = content.value
        self.data.proposal.proposals[proposal_id].is_resolved = True

    def execute_lambda_ops(self, content, proposal_id):
        lambda_ = sp.compute(content)
        operations = lambda_(sp.unit)
        sp.add_operations(operations)
        self.data.proposal.proposals[proposal_id].is_resolved = True


    def execute_proposal(self, proposal_id):
        with self.data.proposal.proposals[proposal_id].content.match_cases() as arg:
            with arg.match("transfer_tez") as proposal_data:
                self.execute_transfer_tez(proposal_data, proposal_id)
            with arg.match("update_agreement_uri") as proposal_data:
                self.execute_update_agreement_uri(proposal_data, proposal_id)
            with arg.match("update_dataset_uri") as proposal_data:
                self.execute_update_dataset_uri(proposal_data, proposal_id)
            with arg.match("update_threshold") as proposal_data:
                self.execute_update_threshold(proposal_data, proposal_id)
            with arg.match("update_generation_duration_minute") as proposal_data:
                self.execute_update_generation_duration_minute(proposal_data, proposal_id)
            with arg.match("update_metadata") as proposal_data:
                self.execute_update_metadata(proposal_data, proposal_id)
            with arg.match("lambda_ops") as proposal_data:
                self.execute_lambda_ops(proposal_data, proposal_id)

    @sp.entry_point
    def create_proposal(self, content, reserve):
        self.zero_tez()
        self.check_member(sp.sender)
        self.check_valid_time()
        sp.set_type(content, proposal_content_type)
        sp.set_type(reserve, sp.TMap(sp.TBytes, sp.TBytes))
        self.validate_proposal(content)
        self.data.proposal.proposals[self.data.proposal.next_proposal_id] = sp.record(
            approved = sp.set([]),
            is_resolved = sp.bool(False),
            proposer = sp.sender,
            create_time = sp.now,
            generation = self.data.info.generation,
            content = content
        )
        self.data.proposal.next_proposal_id += 1
        
    @sp.entry_point
    def sign_proposal(self, proposal_id):
        self.zero_tez()
        self.check_member(sp.sender)
        self.check_valid_time()
        sp.verify(self.data.proposal.proposals.contains(proposal_id), "PROPOSAL_ID_NOT_EXISTED")
        
        proposal = sp.compute(self.data.proposal.proposals[proposal_id])
        sp.verify(~proposal.is_resolved, "PROPOSAL_IS_RESOLVED")
        sp.verify(self.data.info.generation == proposal.generation, "NOT_CURRENT_GENERATION_PROPOSAL")
        sp.verify(~proposal.approved.contains(sp.sender), "PROPOSAL_APPROVED_ALREADY")
        
        self.data.proposal.proposals[proposal_id].approved.add(sp.sender)

    @sp.entry_point
    def resolve_proposal(self, proposal_id):
        self.zero_tez()
        # Check basic limitation
        self.check_valid_time()
        sp.verify(self.data.proposal.proposals.contains(proposal_id), "PROPOSAL_ID_NOT_EXISTED")
        proposal = sp.compute(self.data.proposal.proposals[proposal_id])
        sp.verify(~proposal.is_resolved, "PROPOSAL_IS_RESOLVED")
        sp.verify(self.data.info.generation == proposal.generation, "NOT_CURRENT_GENERATION_PROPOSAL")
        # Check threshold
        sp.verify(self.check_threshold(sp.len(proposal.approved)), "NOT_REACH_THRESHOLD")
        # execute
        self.execute_proposal(proposal_id)

    @sp.entry_point
    def create_event(self, name, description, edition):
        self.zero_tez()
        # check member & valid time
        self.check_member(sp.sender)
        self.check_valid_time()
        sp.set_type(name, sp.TBytes)
        sp.set_type(description, sp.TBytes)
        
        # generate event token ID
        event_token_id = sp.compute(sp.view(
            "get_next_event_token_id", 
            self.data.event.event_token_fa2, 
            sp.unit, 
            sp.TNat
        ).open_some("open get_next_event_token_id view Error"))

        # generate event metadata
        event_token_metadata = sp.view(
            "gen_event_token", 
            self.data.addresses.token_metadata_generator, 
            sp.record(
                creator = sp.self_address,
                event_description = description,
                generation = self.data.info.generation,
                multisig_name = self.data.info.name,
                event_name = name
            ), 
            sp.TMap(sp.TString, sp.TBytes)
        ).open_some("open gen_event_token view Error")

        # create event token
        c_fa2 = sp.contract(
            sp.TList(
                sp.TRecord(
                    is_stewardship = sp.TBool,
                    minter = sp.TAddress,
                    token_info = sp.TMap(sp.TString, sp.TBytes)
                )
            ), 
            self.data.event.event_token_fa2, 
            entry_point = "create_token").open_some()
        sp.transfer(
            sp.list([
                sp.record(
                    is_stewardship = False,
                    minter = sp.self_address,
                    token_info = event_token_metadata
                )
            ]), 
            sp.mutez(0), 
            c_fa2
        )
        
        # record info in storage
        self.data.event.events[self.data.event.next_event_id] = sp.record(
            approved = sp.set([]),
            passed = False,
            proposer = sp.sender,
            create_time = sp.now,
            generation = self.data.info.generation,
            token_id = event_token_id,
            amount = edition,
            claims = sp.map(l={})
        )
        self.data.event.event_id_list.push(self.data.event.next_event_id)
        self.data.event.next_event_id += 1

    @sp.entry_point
    def claim_event(self, public_key, signature, event_id):
        self.zero_tez()
        self.check_valid_time()
        # check public key matching with sender's key hash
        sp.verify(sp.sender == sp.to_address(sp.implicit_account(sp.hash_key(public_key))), "PUBLIC_KEY_ERROR: not matched with sender")
        # check signature 
        payload = sp.view("gen_payload", self.data.addresses.payload_generator, self.data.agreement_uri, sp.TBytes).open_some("open gen_payload view Error")
        sp.verify(sp.check_signature(public_key, signature, payload), "SIGNATURE_NOT_MATCHED")
        event_data = sp.compute(self.data.event.events[event_id])
        # check re-claim
        sp.verify(~event_data.claims.contains(sp.sender), "CANNOT_CLAIM_TWICE")
        # check generation
        sp.verify(self.data.info.generation == event_data.generation, "NOT_CURRENT_GENERATION_EVENT")
        # check amount
        sp.if event_data.amount.is_some():
            event_edition = event_data.amount.open_some("open amount Error")
            # minus the edtion if edtion is limited
            self.data.event.events[event_id].amount = sp.some(sp.as_nat(event_edition - 1, "EVENT_EDITION_INSUFFICIENT"))
        
        # mint event token
        c_fa2 = sp.contract(
            sp.TList(
                sp.TRecord(
                    address = sp.TAddress,
                    amount = sp.TNat,
                    token_id = sp.TNat
                )
            ), 
            self.data.event.event_token_fa2, 
            entry_point = "mint").open_some()
        sp.transfer(
            sp.list([
                sp.record(
                    address = sp.sender,
                    amount = sp.nat(1),
                    token_id = event_data.token_id
                )
            ]), 
            sp.mutez(0), 
            c_fa2
        )
        
        # record signature into storage
        self.data.event.events[event_id].claims[sp.sender] = signature

    @sp.entry_point
    def approve_event(self, event_id):
        self.zero_tez()
        self.check_member(sp.sender)
        self.check_valid_time()
        sp.verify(self.data.event.events.contains(event_id), "EVENT_ID_NOT_EXISTED")
        
        event = sp.compute(self.data.event.events[event_id])
        sp.verify(self.data.info.generation == event.generation, "NOT_CURRENT_GENERATION_PROPOSAL")
        sp.verify(~event.approved.contains(sp.sender), "EVENT_APPROVED_ALREADY")
        
        self.data.event.events[event_id].approved.add(sp.sender)

    @sp.entry_point
    def create_gen0_stewardship(self):
        self.zero_tez()
        # check sender
        sp.verify(sp.sender == self.data.addresses.factory, "ONLY_FACTORY_CAN_CREATE")
        # check generation
        sp.verify(self.data.info.generation == 0, "GENERATION_INCORRECT")
        # check stewardship token id
        sp.verify(self.data.stewardship_token.id == 0, "CREATE_ALREADY")
        
        # generate st token ID
        self.data.stewardship_token.id = sp.compute(sp.view(
            "get_next_stewardship_token_id", 
            self.data.stewardship_token.fa2, 
            sp.unit, 
            sp.TNat
        ).open_some("open get_next_stewardship_token_id view Error"))

        # generate stewardship metadata
        stewardship_token_metadata = sp.view(
            "gen_stewardship_token", 
            self.data.addresses.token_metadata_generator, 
            sp.record(
                generation = sp.nat(1),
                multisig_name = self.data.info.name,
                multisig_description = self.data.info.description,
                creator = sp.self_address
            ), 
            sp.TMap(sp.TString, sp.TBytes)
        ).open_some("open gen_stewardship_token view Error")
        
        # create stewardship token
        c_create_fa2 = sp.contract(
            sp.TList(
                sp.TRecord(
                    is_stewardship = sp.TBool,
                    minter = sp.TAddress,
                    token_info = sp.TMap(sp.TString, sp.TBytes)
                )
            ), 
            self.data.stewardship_token.fa2, 
            entry_point = "create_token").open_some()
        sp.transfer(
            sp.list([
                sp.record(
                    is_stewardship = True,
                    minter = sp.self_address,
                    token_info = stewardship_token_metadata
                )
            ]), 
            sp.mutez(0), 
            c_create_fa2
        )
    
    @sp.entry_point
    def claim_gen0_stewardship(self, public_key, signature):
        self.zero_tez()
        # check generation
        sp.verify(self.data.info.generation == 0, "GENERATION_ERROR")
        # check time
        sp.verify(sp.now <= self.data.timestamp.generation_end_time, "CLAIM_EXPIRED")
        # check public key matching with sender's key hash
        sp.verify(sp.sender == sp.to_address(sp.implicit_account(sp.hash_key(public_key))), "PUBLIC_KEY_ERROR: not matched with sender")
        # check signature 
        payload = sp.view("gen_payload", self.data.addresses.payload_generator, self.data.agreement_uri, sp.TBytes).open_some("open gen_payload view Error")
        sp.verify(sp.check_signature(public_key, signature, payload), "SIGNATURE_NOT_MATCHED")
        # check re-claim
        sp.verify(~self.data.gen0_stewardship_signatures.contains(sp.sender), "CANNOT_CLAIM_TWICE")
        
        # mint stewardship token
        c_fa2 = sp.contract(
            sp.TList(
                sp.TRecord(
                    address = sp.TAddress,
                    amount = sp.TNat,
                    token_id = sp.TNat
                )
            ), 
            self.data.stewardship_token.fa2, 
            entry_point = "mint").open_some()
        sp.transfer(
            sp.list([
                sp.record(
                    address = sp.sender,
                    amount = sp.nat(1),
                    token_id = self.data.stewardship_token.id
                )
            ]), 
            sp.mutez(0), 
            c_fa2
        )
        
        # record signature into storage
        self.data.gen0_stewardship_signatures[sp.sender] = signature

    @sp.entry_point()
    def activate(self):
        self.zero_tez()
        # check generation
        sp.verify(self.data.info.generation == 0, "GENEATION_ERROR")
        # check time
        sp.verify(sp.now > self.data.timestamp.generation_end_time, "STILL_IN_CLAIMING_TIME")
        # check limitation
        st_holders = sp.view("get_token_holders", self.data.stewardship_token.fa2, self.data.stewardship_token.id, sp.TSet(sp.TAddress)).open_some("open get_token_holders view Error")
        holderCount = sp.compute(sp.len(st_holders))
        sp.verify(holderCount >= self.data.threshold.minimum_count, "APPROVE_COUNT_INSUFFICIENT")

        # set to new generation
        self.data.timestamp.generation_start_time = sp.now
        self.data.timestamp.generation_end_time = sp.now.add_minutes(self.data.info.generation_duration_minute)
        self.data.info.generation = 1
    
    @sp.entry_point()
    def reactivate(self):
        self.zero_tez()
        # check generation
        sp.verify(self.data.info.generation > 0, "GENEATION_ERROR")
        # check time
        sp.verify(sp.now > self.data.timestamp.generation_end_time, "STILL_IN_GENERATION_TIME")

        # calculate apporval in all events 
        newStHolders = sp.local("newStHolders", sp.map(l={}, tkey=sp.TAddress, tvalue=sp.TNat))
        sp.for event_id in self.data.event.event_id_list:
            event_data = sp.compute(self.data.event.events[event_id])
            sp.if self.check_threshold(sp.len(event_data.approved)):
                self.data.event.events[event_id].passed = True
                event_holders = sp.view("get_token_holders", self.data.event.event_token_fa2, event_data.token_id, sp.TSet(sp.TAddress)).open_some("open get_token_holders view Error")
                sp.for holder in event_holders.elements():
                    sp.if ~newStHolders.value.contains(holder):
                        newStHolders.value[holder] = 0
                    newStHolders.value[holder] += 1
        
        # check limitation
        sp.verify(sp.len(newStHolders.value) >= self.data.threshold.minimum_count, "NEW_ST_HOLDER_COUNT_INSUFFICIENT")

        # generate st token ID
        self.data.stewardship_token.id = sp.view(
            "get_next_stewardship_token_id", 
            self.data.stewardship_token.fa2, 
            sp.unit, 
            sp.TNat
        ).open_some("open get_next_stewardship_token_id view Error")

        # generate stewardship metadata
        stewardship_token_metadata = sp.view(
            "gen_stewardship_token", 
            self.data.addresses.token_metadata_generator, 
            sp.record(
                generation = self.data.info.generation + 1,
                multisig_name = self.data.info.name,
                multisig_description = self.data.info.description,
                creator = sp.self_address
            ), 
            sp.TMap(sp.TString, sp.TBytes)
        ).open_some("open gen_stewardship_token view Error")
        
        # create stewardship token
        c_create_fa2 = sp.contract(
            sp.TList(
                sp.TRecord(
                    is_stewardship = sp.TBool,
                    minter = sp.TAddress,
                    token_info = sp.TMap(sp.TString, sp.TBytes)
                )
            ), 
            self.data.stewardship_token.fa2, 
            entry_point = "create_token").open_some()
        sp.transfer(
            sp.list([
                sp.record(
                    is_stewardship = True,
                    minter = sp.self_address,
                    token_info = stewardship_token_metadata
                )
            ]), 
            sp.mutez(0), 
            c_create_fa2
        )

        mintList = sp.local("mintList", sp.list([]))
        sp.for stHolder in newStHolders.value.items():
            mintList.value.push(
                sp.record(
                    address = stHolder.key,
                    amount = stHolder.value,
                    token_id = self.data.stewardship_token.id
                )
            )

        c_mint_fa2 = sp.contract(
            sp.TList(
                sp.TRecord(
                    address = sp.TAddress,
                    amount = sp.TNat,
                    token_id = sp.TNat
                )
            ), 
            self.data.event.event_token_fa2, 
            entry_point = "mint").open_some()
        sp.transfer(
            mintList.value, 
            sp.mutez(0), 
            c_mint_fa2
        )
        
        # set to new generation
        self.data.timestamp.generation_start_time = sp.now
        self.data.timestamp.generation_end_time = sp.now.add_minutes(self.data.info.generation_duration_minute)
        self.data.info.generation += 1
        self.data.event.event_id_list = sp.list([])

    
    @sp.onchain_view()
    def is_alive(self):
        sp.result((self.data.info.generation > 0) & (sp.now <= self.data.timestamp.generation_end_time))
        
    @sp.onchain_view()
    def get_all_user(self):
        sp.result(sp.view("get_token_holders", self.data.stewardship_token.fa2, self.data.stewardship_token.id, sp.TSet(sp.TAddress)).open_some("open view Error"))
        
        
@sp.add_test(name = "DID-MultiSig Test")
def test():
    scenario = sp.test_scenario()
    
    scenario.h1("DID-MultiSig contract")
    c = MultiSig()
    scenario += c
    
    scenario.h2("DID-Contract Factory")

    addressesMap = {}
    addressesMap["admin"] = Admin
    addressesMap["stewardship_token_fa2"] = TokenFA2
    addressesMap["event_token_fa2"] = TokenFA2
    addressesMap["token_metadata_generator"] = TokenMetadataGenerator
    addressesMap["payload_generator"] = PayloadGenerator

    addresses = sp.big_map(
        tkey = sp.TString,
        tvalue = sp.TAddress,
        l = addressesMap
    )
    
    c_factory = MultiSigFactory(addresses)
    scenario += c_factory

    # c_factory.create_multisig(
    #     name = sp.utils.bytes_of_string("123River"), 
    #     agreement_uri = sp.string("ipfs://agreement"), 
    #     dataset_uri = sp.string("ipfs://prompt"), 
    #     contract_metadata = sp.utils.bytes_of_string("ipfs://123River-metadata")
    # )