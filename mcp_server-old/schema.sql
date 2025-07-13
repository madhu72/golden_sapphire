COMMENT ON TABLE amf_action IS 'Stored list of actions that can be performed in AMF';
CREATE TABLE amf_action (
        action_id UUID NOT NULL,
        action_name TEXT NOT NULL,
        action_type TEXT NOT NULL,
        parameter JSONB NOT NULL,
        description TEXT NOT NULL,
        active BOOL NOT NULL,
        user_audit_info JSONB NOT NULL,
        CONSTRAINT "primary" PRIMARY KEY (action_id)
);
COMMENT ON TABLE amf_auditlog IS 'Audit log table to track actions performed in AMF';
CREATE TABLE amf_auditlog (
        id UUID NOT NULL,
        entity_name TEXT NOT NULL,
        action_performed TEXT NOT NULL,
        appuser_id UUID NOT NULL,
        performed_on TIMESTAMPTZ NOT NULL,
        reference_id UUID NOT NULL,
        remarks JSONB NOT NULL,
        CONSTRAINT "primary_auditlog" PRIMARY KEY (id)
);
COMMENT ON TABLE amf_comm_profile IS 'Table to store communication profiles for different protocols';
CREATE TABLE amf_comm_profile (
        protocol_id UUID NOT NULL,
        mailbox_id UUID NOT NULL,
        comm_type TEXT NOT NULL,
        operation TEXT NOT NULL,
        protocol_name TEXT NOT NULL,
        parameter JSONB NOT NULL,
        active BOOL NOT NULL,
        user_audit_info JSONB NOT NULL,
        status_action TEXT NOT NULL,
        profile_name TEXT NOT NULL,
        CONSTRAINT "primary_comm_profile" PRIMARY KEY (protocol_id)
);
COMMENT ON TABLE amf_comm_rule IS 'List of rules for communication actionst that is for delivery of messages';
CREATE TABLE amf_comm_rule (
        rule_id UUID NOT NULL,
        sender TEXT NOT NULL,
        receiver TEXT NOT NULL,
        msg_type TEXT NOT NULL,
        action_id UUID NOT NULL,
        active BOOL NOT NULL,
        user_audit_info JSONB NOT NULL,
        delivery_type TEXT NULL DEFAULT 'Scheduled',
        communications_workflow TEXT NULL,
        delivery TEXT NULL DEFAULT 'Default Delivery',
        bp_name TEXT NULL,
        schedule_name TEXT NULL,
        schedule_status TEXT NULL DEFAULT 'start schedule',
        CONSTRAINT "primary_commrule_id" PRIMARY KEY (rule_id)
);

COMMENT ON TABLE amf_customer IS 'List of customers in AMF';
CREATE TABLE amf_customer (
        customer_id UUID NOT NULL,
        customer TEXT NOT NULL,
        billing_id TEXT NOT NULL,
        email TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        user_audit_info JSONB NOT NULL,
        active BOOL NOT NULL,
        CONSTRAINT "primary_customer" PRIMARY KEY (customer_id)
);

COMMENT ON TABLE amf_delivery IS 'Table to store delivery information for messages';
CREATE TABLE amf_delivery (
        delivery_id UUID NOT NULL,
        time_queued TIMESTAMPTZ NOT NULL,
        message_id UUID NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        message_type TEXT NOT NULL,
        next_time TIMESTAMPTZ NOT NULL,
        sender TEXT NOT NULL,
        receiver TEXT NOT NULL,
        status TEXT NOT NULL,
        orig_file TEXT NULL,
        deleted BOOL NULL DEFAULT false,
    locked BOOL NULL DEFAULT false,
        CONSTRAINT "primary_delivery" PRIMARY KEY (delivery_id)
);

COMMENT ON TABLE amf_event IS 'Events occurred during message processing';
CREATE TABLE amf_event (
        event_id UUID NOT NULL,
        level TEXT NULL,
        message_id UUID NULL,
        session_id UUID NOT NULL,
        action_id UUID NULL,
        text TEXT NULL,
        status TEXT NOT NULL,
        create_time TIMESTAMPTZ NOT NULL,
        created_by TEXT NOT NULL,
        CONSTRAINT "primary_event" PRIMARY KEY (event_id)
);
CREATE INDEX  amf_event_session_id_idx on amf_event (session_id ASC);
CREATE INDEX  amf_event_create_time_idx on amf_event(create_time ASC);

CREATE TABLE amf_feedback (
        fb_id UUID NOT NULL,
        user_id UUID NOT NULL,
        request_type TEXT NOT NULL,
        details TEXT NOT NULL,
        status INT NOT NULL,
        user_audit_info JSONB NOT NULL,
        CONSTRAINT "primary_feedback" PRIMARY KEY (fb_id)
);

CREATE TABLE amf_file_upload (
        file_id UUID NOT NULL,
        document TEXT NOT NULL,
        document_type TEXT NOT NULL,
        protocol_name TEXT NOT NULL,
        document_name TEXT NOT NULL,
        file_updated BOOL NOT NULL,
        CONSTRAINT "primary_amf_file_upload" PRIMARY KEY (file_id)
);

CREATE TABLE amf_fw_rules (
        fw_rule_id UUID NOT NULL,
        business_need TEXT NOT NULL,
        source_ip TEXT NOT NULL,
        source_server_name TEXT NOT NULL,
        destination_ip TEXT NOT NULL,
        destination_server_name TEXT NOT NULL,
        protocol TEXT NOT NULL,
        port_number TEXT NOT NULL,
        duration TEXT NOT NULL,
        additional_details TEXT NOT NULL,
        user_audit_info JSONB NOT NULL,
        CONSTRAINT "primary_amf_fw_rules" PRIMARY KEY (fw_rule_id)
);

CREATE TABLE amf_import_document (
        doc_id UUID NOT NULL,
        document_name TEXT NOT NULL,
        file_name TEXT NOT NULL,
        user_audit_info JSONB NOT null,
        CONSTRAINT "primary_amf_import_document" PRIMARY KEY (doc_id)

);

CREATE TABLE amf_import_transactions (
        trans_id UUID NOT NULL,
        reference_id UUID NOT NULL,
        import_type TEXT NOT NULL,
        response_code TEXT NOT NULL,
        notes TEXT NOT NULL,
        raw_data JSONB NOT NULL,
        user_audit_info JSONB NOT NULL,
        CONSTRAINT "primary_amf_import_transactions" PRIMARY KEY (trans_id)
);

CREATE TABLE amf_match (
        sender TEXT NOT NULL,
        match_id UUID NOT NULL,
        receiver TEXT NULL,
        message_type TEXT NOT NULL,
        precedence INT NULL,
        regex TEXT NOT NULL,
        user_audit_info JSONB NOT NULL,
        regular_expression BOOL NULL DEFAULT false,
        CONSTRAINT "primary_amf_match" PRIMARY KEY (match_id)
);

CREATE INDEX  amf_match_sender_idx on amf_match(sender ASC);

COMMENT ON TABLE amf_message IS 'Table to store messages in AMF';
CREATE TABLE amf_message (
        sender TEXT NOT NULL,
        receiver TEXT NOT NULL,
        msg_type TEXT NOT NULL,
        control_no TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_path TEXT NOT NULL,
        workflow_id TEXT NULL,
        session_id UUID NULL,
        parent_id UUID NULL,
        doc_count INT NULL,
        origin TEXT NOT NULL,
        reference_id JSONB NULL,
        status TEXT NOT NULL,
        status_time TIMESTAMPTZ NOT NULL,
        can_requeue BOOL NOT NULL,
        can_reprocess BOOL NOT NULL,
        create_time TIMESTAMPTZ NOT NULL,
        created_by TEXT NOT NULL,
        message_id UUID NOT NULL,
        file_size INT8 NOT NULL,
        site_id TEXT NULL,
        node_id TEXT NULL,
        can_req_and_rep BOOL NULL DEFAULT false,
        data_type TEXT NULL DEFAULT 'External',
        contents bytea NULL,
        CONSTRAINT "primary_amf_message" PRIMARY KEY (message_id)
);
CREATE INDEX  amf_message_create_time_idx on amf_message(create_time DESC);
CREATE INDEX  amf_message_sender_idx on amf_message(sender ASC);
CREATE INDEX  amf_message_receiver_idx on amf_message(receiver ASC);
CREATE INDEX  amf_message_msg_type_idx on amf_message(msg_type ASC);
CREATE INDEX  amf_message_file_name_idx on amf_message(file_name ASC);
CREATE INDEX  amf_message_session_id_idx on amf_message(session_id ASC);

CREATE TABLE amf_message_note (
        note_id UUID NOT NULL,
        message_id UUID NOT NULL,
        notes TEXT NOT NULL,
        user_audit_info JSONB NOT NULL,
        reference_name TEXT NULL,
        CONSTRAINT "primary_amf_message_note" PRIMARY KEY (note_id)
);
CREATE TABLE amf_message_type (
        type_id UUID NOT NULL,
        message_type TEXT NOT NULL,
        description TEXT NOT NULL,
        active BOOL NOT NULL,
        user_audit_info JSONB NOT NULL,
        CONSTRAINT "primary_amf_message_type" PRIMARY KEY (type_id)
);
CREATE INDEX  amf_messagetypes_message_type_idx on amf_message_type(message_type ASC, active ASC);
CREATE TABLE amf_onb_node_status (
        status_id UUID NOT NULL,
        session_id UUID NOT NULL,
        node_id TEXT NOT NULL,
        node_deployed TEXT NOT NULL,
        action_name TEXT NOT NULL,
        create_time TIMESTAMPTZ NOT NULL,
        status TEXT NOT NULL,
        CONSTRAINT "primary_amf_onb_node_status" PRIMARY KEY (status_id)
);
CREATE TABLE amf_onb_status (
        session_id UUID NOT NULL,
        session_name TEXT NOT NULL,
        transaction_id UUID NOT NULL,
        node_list TEXT NOT NULL,
        start_time TIMESTAMPTZ NOT NULL,
        end_time TIMESTAMPTZ NULL,
        status TEXT NOT NULL,
        CONSTRAINT "primary_amf_onb_status" PRIMARY KEY (session_id)
);
CREATE TABLE amf_privileges (
        privilege_id UUID NOT NULL,
        privilege_name TEXT NOT NULL,
        uri TEXT NOT NULL,
        method TEXT NOT NULL,
        active_status BOOL NOT NULL,
        created_by TEXT NOT NULL,
        create_time TIMESTAMPTZ NOT NULL,
        order_no INT NULL,
        action TEXT NOT NULL,
        component_type TEXT NOT NULL,
        CONSTRAINT "primary_amf_privileges" PRIMARY KEY (privilege_id)
);
CREATE TABLE amf_property (
        property_id UUID NOT NULL,
        service VARCHAR NOT NULL,
        key VARCHAR(20) NOT NULL,
        value VARCHAR(100) NULL,
        CONSTRAINT amf_property_pk PRIMARY KEY (property_id)
);
CREATE INDEX  amf_property_service_idx on amf_property(service ASC);

CREATE TABLE amf_service_status (
        service_status_id UUID NOT NULL,
        service_name TEXT NOT NULL,
        service_type TEXT NOT NULL,
        status TEXT NOT NULL,
        version TEXT NOT NULL,
        errors TEXT NOT NULL,
        create_time TIMESTAMPTZ NOT NULL,
        created_by TEXT NOT NULL,
        CONSTRAINT "primary_amf_service_status" PRIMARY KEY (service_status_id)
);
CREATE TABLE amf_session (
        session_id UUID NOT NULL,
        session_start TIMESTAMPTZ NOT NULL,
        session_end TIMESTAMPTZ NULL,
        workflow_name TEXT NOT NULL,
        instance_id TEXT NOT NULL,
        username TEXT NOT NULL,
        status TEXT NOT NULL,
        create_time TIMESTAMPTZ NOT NULL,
        created_by TEXT NOT NULL,
        site_id TEXT NULL,
        node_id TEXT NULL,
        CONSTRAINT "primary_amf_session" PRIMARY KEY (session_id)
);
CREATE INDEX  amf_session_session_start_idx on amf_session(session_start DESC);

CREATE TABLE amf_session_rel (
        relation_id UUID NOT NULL,
        session_id UUID NOT NULL,
        message_id UUID NOT NULL,
        rel_type TEXT NOT NULL,
        create_time TIMESTAMPTZ NOT NULL,
        created_by TEXT NOT NULL,
        CONSTRAINT "primary_amf_session_rel" PRIMARY KEY (relation_id)
);

CREATE INDEX  amf_session_rel_message_id_idx on amf_session_rel(message_id ASC);

CREATE TABLE amf_ufagent_downloads (
        ufa_id UUID NOT NULL,
        hostname TEXT NOT NULL,
        os_name TEXT NOT NULL,
        os_type TEXT NOT NULL,
        ufa_home TEXT NOT NULL,
        note TEXT NULL,
        user_audit_info JSONB NOT NULL,
        username TEXT NOT NULL,
        assigned_to TEXT NULL,
        active BOOL NULL DEFAULT true,
        ufa_version TEXT NULL DEFAULT '1.0',
        debug_level TEXT NULL,
        CONSTRAINT "primary_amf_ufagent_downloads" PRIMARY KEY (ufa_id)
);

COMMENT ON TABLE amf_user IS 'Users associated with AMF for transmission of files and messages';
CREATE TABLE amf_user (
        mailbox_id UUID NOT NULL,
        mailbox TEXT NOT NULL,
        user_name TEXT NOT NULL,
        password TEXT NOT NULL,
        customer_id UUID NOT NULL,
        given_name TEXT NOT NULL,
        surname TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        email TEXT NOT NULL,
        active BOOL NOT NULL,
        user_audit_info JSONB NOT NULL,
        transaction_id UUID NOT NULL,
        updated BOOL NOT NULL,
        attempt_no INT NOT NULL,
        user_type TEXT NOT NULL,
        status_action TEXT NOT NULL,
        use_global_mailbox BOOL NOT NULL,
        provider_details JSONB NOT NULL,
        authentication_type TEXT NOT NULL,
        additional_info TEXT NOT NULL,
        parameter JSONB NOT NULL default '{}',
        CONSTRAINT "primary_amf_user" PRIMARY KEY (mailbox_id)
);

CREATE INDEX  amf_user_mailbox_idx on amf_user (mailbox ASC);
CREATE TABLE amf_user_alt (
        user_alt_id UUID NOT NULL,
        mailbox_id UUID NOT NULL,
        user_name TEXT NOT NULL,
        user_id UUID NOT NULL,
        created_by TEXT NOT NULL,
        create_time TIMESTAMPTZ NOT NULL,
        CONSTRAINT "primary_amf_user_alt" PRIMARY KEY (user_alt_id)
);

CREATE TABLE amf_wfqueue (
        queue_id UUID NOT NULL,
        queue_name TEXT NOT NULL,
        active BOOL NOT NULL,
        CONSTRAINT "primary_amf_wfqueue" PRIMARY KEY (queue_id)
);

CREATE TABLE amf_workflow (
        workflow_id UUID NOT NULL,
        name TEXT NOT NULL,
        description TEXT NULL,
        user_audit_info JSONB NOT NULL,
        active BOOL NOT NULL,
        communications_workflow BOOL NULL DEFAULT false,
        CONSTRAINT "primary_amf_workflow" PRIMARY KEY (workflow_id)
);
CREATE TABLE amf_workflow_step (
        step_id UUID NOT NULL,
        step_no INT NOT NULL,
        workflow_id UUID NOT NULL,
        action_id UUID NOT NULL,
        description TEXT NOT NULL,
        active BOOL NOT NULL,
        user_audit_info JSONB NOT NULL,
        CONSTRAINT "primary_amf_workflow_step" PRIMARY KEY (step_id)
);
CREATE INDEX  amf_wf_step_workflow_id_idx on amf_workflow_step(workflow_id);
CREATE TABLE amf_mftlinks (
        id UUID NOT NULL,
        datacenter_name TEXT NOT NULL,
        category TEXT NOT NULL,
        nodes JSONB NOT NULL,
        user_audit_info JSONB NOT NULL,
        CONSTRAINT "primary_amf_mftlinks" PRIMARY KEY (id)
);


CREATE TABLE amf_queue_definitions (
queue_id UUID NOT NULL,
queue_name TEXT NOT NULL,
description TEXT NULL,
queue_type TEXT NOT NULL,
queue_manager TEXT NOT NULL,
username TEXT NOT NULL,
password TEXT NOT NULL,
channel TEXT NOT NULL,
host TEXT NOT NULL,
port INT NOT NULL,
priority BOOL NULL DEFAULT false,
fifo BOOL NULL DEFAULT false,
warndepth BOOL NULL DEFAULT false,
maxdepth BOOL NULL DEFAULT false,
user_audit_info JSONB NOT NULL,
active BOOL NOT NULL,
CONSTRAINT "primary_amf_queue_definitions" PRIMARY KEY (queue_id)
);


CREATE TABLE amf_providers (
provider_id UUID NOT NULL,
provider_name TEXT NOT NULL,
description TEXT NOT NULL,
provider_type TEXT NOT NULL,
user_audit_info JSONB NOT NULL,
active BOOL NOT NULL,
CONSTRAINT "primary_amf_providers" PRIMARY KEY (provider_id)

);
CREATE TABLE amf_platforms (
platform_id UUID NOT NULL,
provider_id UUID NOT NULL,
platform_name TEXT NOT NULL,
platform_type TEXT NOT NULL,
service_names TEXT NOT NULL,
service_names_prefix TEXT NOT NULL,
user_audit_info JSONB NOT NULL,
configuration JSONB NOT NULL,
CONSTRAINT "primary_amf_platforms" PRIMARY KEY (platform_id)

);

CREATE TABLE amf_role_privileges (
        role_privilege_id UUID NOT NULL,
        role TEXT NOT NULL,
        privilege UUID NOT NULL,
        user_audit_info JSONB NOT NULL,
        group_id UUID NOT NULL,
        CONSTRAINT "primary_role_privileges" PRIMARY KEY (role_privilege_id)
);

CREATE TABLE QT_amf_wf_registration_queue (
queue_id UUID NOT NULL,
queue_data text not null,
queued_time TIMESTAMPTZ NOT NULL,
queued_by text not null,
CONSTRAINT "primary_amf_wf_registration_queue" PRIMARY KEY (queue_id)
);

CREATE TABLE QT_amf_wf_input_queue (
queue_id UUID NOT NULL,
queue_data text not null,
queued_time TIMESTAMPTZ NOT NULL,
queued_by text not null,
CONSTRAINT "primary_amf_wf_input_queue" PRIMARY KEY (queue_id)
);

CREATE TABLE QT_sfg_wf_output_queue (
queue_id UUID NOT NULL,
queue_data text not null,
queued_time TIMESTAMPTZ NOT NULL,
queued_by text not null,
CONSTRAINT "primary_sfg_wf_output_queue" PRIMARY KEY (queue_id)
);

CREATE TABLE QT_amf_wf_comms_queue (
queue_id UUID NOT NULL,
queue_data text not null,
queued_time TIMESTAMPTZ NOT NULL,
queued_by text not null,
CONSTRAINT "primary_amf_wf_comms_queue" PRIMARY KEY (queue_id)
);

CREATE TABLE QT_amf_wf_error_queue (
queue_id UUID NOT NULL,
queue_data text not null,
queued_time TIMESTAMPTZ NOT NULL,
queued_by text not null,
CONSTRAINT "primary_amf_wf_error_queue" PRIMARY KEY (queue_id)
);

CREATE TABLE QT_amf_wf_commserror_error (
queue_id UUID NOT NULL,
queue_data text not null,
queued_time TIMESTAMPTZ NOT NULL,
queued_by text not null,
CONSTRAINT "primary_amf_wf_commserror_error" PRIMARY KEY (queue_id)
);


CREATE TABLE QT_amf_wf_onbregistration_queue (
queue_id UUID NOT NULL,
queue_data text not null,
queued_time TIMESTAMPTZ NOT NULL,
queued_by text not null,
CONSTRAINT "primary_amf_wf_onbregistration_queue" PRIMARY KEY (queue_id)
);

CREATE TABLE QT_amf_wf_onbinput_queue (
queue_id UUID NOT NULL,
queue_data text not null,
queued_time TIMESTAMPTZ NOT NULL,
queued_by text not null,
CONSTRAINT "primary_amf_wf_onbinput_queue" PRIMARY KEY (queue_id)
);

CREATE TABLE amf_menu_toggle (
        menu_id UUID NOT NULL,
        user_name TEXT NOT NULL,
        enable_new_menu BOOL NOT NULL,
        create_time TIMESTAMPTZ NOT NULL,
        created_by TEXT NOT NULL,
        CONSTRAINT "primary_menu_toggle" PRIMARY KEY (menu_id)
);

CREATE TABLE amf_venafi (
        cert_id UUID NOT NULL,
        name TEXT NOT NULL,
        subject TEXT NOT NULL,
        alt_ips TEXT NULL,
        alt_dns TEXT NULL,
        environment TEXT NULL,
        organization TEXT NULL,
        city TEXT NULL,
        state TEXT NULL,
        country TEXT NULL,
        guid TEXT NULL,
        certificatedn TEXT NULL,
        status TEXT NOT NULL,
        active BOOL NOT NULL,
        user_audit_info JSONB NOT NULL,
        CONSTRAINT "primary_cert_id" PRIMARY KEY (cert_id)
);

CREATE TABLE amf_email_templates (
        template_id UUID NOT NULL,
        template_name TEXT NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        user_audit_info JSONB NOT NULL,
        active BOOL NOT NULL,
        CONSTRAINT "primary_amf_email_templates" PRIMARY KEY (template_id)
);

CREATE TABLE amf_ufa_stats (
        ufa_stats_id UUID NOT NULL,
        username TEXT NOT NULL,
        mode TEXT NOT NULL,
        file_name TEXT NOT NULL,
        start_time TIMESTAMPTZ NOT NULL,
        end_time TIMESTAMPTZ NOT NULL,
        time_taken TEXT NOT NULL,
        create_time TIMESTAMPTZ NOT NULL,
        file_size bigint NOT NULL,
        notes TEXT NULL,
        CONSTRAINT "primary_amf_ufa_stats" PRIMARY KEY (ufa_stats_id)
);


CREATE TABLE amf_configuration (
        config_id UUID NOT NULL,
        parameter_type TEXT NOT NULL,
        parameter JSONB NOT NULL,
        user_audit_info JSONB NOT NULL,
        CONSTRAINT "primary_config_id" PRIMARY KEY (config_id)
);

CREATE TABLE amf_schedule_activity (
        schedule_activity_id UUID NOT NULL,
        rule_id UUID NOT NULL,
        schedule_name TEXT NOT NULL,
        create_time TIMESTAMPTZ NULL,
        status TEXT NOT NULL,
        active BOOL NOT NULL,
        response TEXT NOT NULL,
        user_audit_info JSONB NOT NULL,
        CONSTRAINT primary_schedule_actcivity_id PRIMARY KEY (schedule_activity_id)
);

CREATE TABLE schedule_monitor (
        instance_id UUID NOT NULL,
        create_time TIMESTAMPTZ NULL,
        update_time TIMESTAMPTZ NULL,
        status TEXT NOT NULL,
        service_type TEXT NOT NULL,
        notes TEXT NOT NULL,
        CONSTRAINT primary_schedule_monitor PRIMARY KEY (instance_id)
);

CREATE TABLE retry_schedules (
        rschedule_id UUID NOT NULL,
        delivery_id TEXT NOT NULL,
        message_id TEXT NOT NULL,
        status TEXT NOT NULL,
        last_interval int,
        CONSTRAINT primary_retry_schedules PRIMARY KEY (rschedule_id)
);

create index concurrently amf_delivery_update_0001_ndx on amf_delivery(next_time,status, sender, receiver,message_type);
create index concurrently ndx_read_delivery on amf_delivery(sender, receiver, message_type,time_queued, file_name,file_path, orig_file, locked, deleted, next_time);

CREATE TABLE amf_providers_config (
        provider_config_id UUID NOT NULL,
        provider_type TEXT NOT NULL,
        providers TEXT NOT NULL,
        user_audit_info JSONB NOT NULL,
        CONSTRAINT primary_amf_providers_config PRIMARY KEY (provider_config_id)
);


CREATE TABLE amf_platform_config (
        platform_config_id UUID NOT NULL,
        provider TEXT NOT NULL,
        platforms TEXT NOT NULL,
        user_audit_info JSONB NOT NULL,
        CONSTRAINT primary_amf_platforms_config PRIMARY KEY (platform_config_id)
);


CREATE TABLE amf_platform_field_config (
        platform_field_config_id UUID NOT NULL,
        provider TEXT NOT NULL,
        platform TEXT NOT NULL,
        field_config TEXT NOT NULL,
        user_audit_info JSONB NOT NULL,
        CONSTRAINT primary_amf_platform_field_config PRIMARY KEY (platform_field_config_id)
);

ALTER TABLE amf_user ADD approved_by TEXT NULL;
ALTER TABLE amf_user ADD approval_status TEXT NULL;


CREATE TABLE sftpd_mgr (
   unique_id UUID NOT NULL,
   message_id UUID NOT NULL,
   file_owner TEXT,
   file_path TEXT,
   upload_path TEXT,
   create_time TIMESTAMPTZ NOT NULL default current_timestamp,
   CONSTRAINT primary_sftpd_mgr PRIMARY KEY (unique_id)
);

CREATE TABLE amf_branding_config (
        branding_config_id UUID NOT NULL,
        client_name TEXT NOT NULL,
        config JSONB NOT NULL,
        user_audit_info JSONB NOT NULL,
        CONSTRAINT primary_branding_config_id PRIMARY KEY (branding_config_id)
);


CREATE TABLE amf_schedule (
        schedule_id UUID NOT NULL,
        schedule_name TEXT NOT NULL,
        schedule_type TEXt NOT NULL,
        parameter JSONB NOT NULL,
        active BOOL NOT NULL,
        user_audit_info JSONB NOT NULL,
        CONSTRAINT primary_schedule_id PRIMARY KEY (schedule_id)
);

CREATE TABLE amf_message_delivery (
transaction_id UUID NOT NULL,
message_id UUID NOT NULL,
sender text not null,
receiver text not null,
msgtype text not null,
filename text not null,
filepath text not null,
updated_at TIMESTAMPTZ NOT NULL,
CONSTRAINT "primary_amf_message_delivery" PRIMARY KEY (transaction_id)
);



CREATE TABLE amf_running_jobs (
transaction_id UUID NOT NULL,
sender text not null,
receiver text not null,
msgtype text not null,
updated_at TIMESTAMPTZ NOT NULL,
CONSTRAINT "primary_amf_running_jobs" PRIMARY KEY (transaction_id)
);

CREATE TABLE delivery_running_status (
scheduler_id UUID NOT NULL,
sender text not null,
receiver text not null,
msgtype text not null,
running boolean not null,
create_time TIMESTAMPTZ NOT NULL,
update_time TIMESTAMPTZ NOT NULL,
CONSTRAINT "primary_scheduler_status" PRIMARY KEY (scheduler_id)
);

CREATE TABLE amf_settings (
setting_id UUID NOT NULL,
config_type TEXT NOT NULL,
config JSONB NOT NULL,
user_audit_info JSONB NOT NULL,
CONSTRAINT "primary_amf_settings" PRIMARY KEY (setting_id)
);

insert into amf_platforms(platform_id, provider_id,platform_name,platform_type,service_names,service_names_prefix,user_audit_info,configuration) values(gen_random_uuid(),'ed8f290d-a76a-48bb-ae98-48331682ad0e','SFG-TM','SFG-TM','','','{"created_by": "CMD", "created_on": "2022-01-01 00:00:01.000", "last_modified_by": "", "last_modified_on": ""}','{"api_password": "jtPV6FmhjgGUf-QqUTcP1mAfOS_Lm0IKAsyK5WBghx8", "api_port": 40074, "api_user": "amf_api_user", "base_port": 40000, "cd_netmap": "", "community_name": "AMF_COMM", "node_names": "localhost", "routing_rule": "AMF_BP_REGISTER_INPUT_TM", "ssl": false}');

CREATE TABLE scheduler_status (
scheduler_id UUID NOT NULL,
running BOOL NOT NULL,
create_time TIMESTAMPTZ NOT NULL,
update_time TIMESTAMPTZ NOT NULL,
CONSTRAINT "primary_scheduler_status" PRIMARY KEY (scheduler_id)
);

CREATE TABLE sample_data_status (
sample_data_id UUID NOT NULL,
name text not null,
installed bool not null,
running bool not null,
user_audit_info JSONB NOT NULL,
CONSTRAINT "primary_sample_data_status" PRIMARY KEY (sample_data_id)
);

CREATE TABLE amf_rule (
                          rule_id UUID NOT NULL,
                          sender TEXT NOT NULL,
                          receiver TEXT NOT NULL,
                          msg_type TEXT NOT NULL,
                          workflow_id UUID NOT NULL,
                          active BOOL NOT NULL,
                          queue_name TEXT NOT NULL,
                          user_audit_info JSONB NOT NULL,
                          archive_flag BOOL NOT NULL DEFAULT false,
                          noaction BOOL NOT NULL DEFAULT false,
                          na_status TEXT NOT NULL DEFAULT '',
                          mailbox_flag BOOL DEFAULT false,
                          CONSTRAINT "primary_amf_rule" PRIMARY KEY (rule_id)
);
CREATE INDEX  amf_rules_sender_idx on amf_rule(sender ASC, receiver ASC, msg_type ASC, active ASC);

CREATE TABLE amf_ai_scripts (
ai_id UUID NOT NULL,
prompt TEXT NOT NULL,
classname TEXT NOT NULL,
filename TEXT NOT NULL,
script TEXT NOT NULL,
user_audit_info JSONB NOT NULL,
CONSTRAINT "primary_amf_ai_scripts" PRIMARY KEY (ai_id)
);

CREATE TABLE amf_okta_users (
	user_name TEXT NOT NULL,
	user_id TEXT NOT NULL,
    response JSONB NOT NULL,
    CONSTRAINT "primary_okta_users" PRIMARY KEY (user_id)
);

CREATE TABLE process_status (
    id INT PRIMARY KEY DEFAULT unique_rowid(),
    sender TEXT,
    receiver TEXT,
    process_number TEXT,
    status TEXT,
    result JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE visualizer (
    visualizer_id UUID NOT NULL,
    workflow_name TEXT,
    nodes JSONB,
    edges JSONB,
	 CONSTRAINT "primary_visualizer_id" PRIMARY KEY (visualizer_id)
	);
	
CREATE TABLE workflow_details (
    transaction_id UUID NOT NULL,
	workflow_id UUID NOT NULL,
	parameters JSONB,
	created_on TIMESTAMPTZ DEFAULT NOW()
);
CREATE SEQUENCE process_status_id_seq;
create table process_status_sessions (
session_id INT PRIMARY KEY DEFAULT unique_rowid(),
batch_activity_id integer,
 created_at timestamp with time zone default now()
);
 
create table process_status_session_logs (
transaction_id INT PRIMARY KEY DEFAULT unique_rowid(),
session_id integer,
    log_type text not null,
    log_message text,
    created_at timestamp with time zone default now()
);

create table cd_process_numbers
(
    transaction_id uuid primary key,
    delivery_id uuid,
    message_id uuid,
    process_number string,
    status string default 'Submitted'
);

CREATE TABLE amf_user_association (
user_id UUID NOT NULL,
admin_user TEXT NOT NULL,
onb_user TEXT NOT NULL,
default_receiver TEXT NOT NULL,
default_msgtype TEXT NOT NULL,
user_audit_info JSONB NOT NULL,
active BOOL NOT NULL DEFAULT true,
CONSTRAINT "primary_amf_user_association" PRIMARY KEY (user_id)
);

INSERT INTO amf_settings (setting_id, config_type, config, user_audit_info)
VALUES ('032d1b31-9ce3-4617-bb5f-3a9c785fa800', 'AMF Settings',
        '{
          "APP_BUTTON_BACKGROUND_COLOR": "#265280",
          "APP_FAVICON_TYPE": "image/png",
          "APP_FAVICON_URL": "/resources/img/adi-favicon.png",
          "APP_LOGO_STYLES": "width:203px;margin-left:10px;margin-top:10px;",
          "APP_LOGO_URL": "/resources/img/agiledatainc-200X50.png",
          "APP_NAVBAR_HOVER_COLOR": "#5897ce",
          "Apptitle": "AMF Dashboard",
          "CDReceiveDisable": "True",
          "CERTFILE": "certs/server.crt",
          "COMMUNITY_NAME": "AMF_COMM",
          "COPYRIGHT_TEXT": "2024-25 Agile Data Inc, All rights are reserved.",
          "CREATE_BP_IN_SFG": "CREATE_BP_IN_SFG",
          "DEFAULT_PAGE_SIZE": "23",
          "DEFAULT_SCREEN": "Message Activity",
          "DISABLE_SFTP_GET": "false",
          "EnableGlobalMailbox": "True",
          "EnableVenafi": "Yes",
          "Environments": "Prod,Non-Prod",
          "FOOTER_BACKGROUND_COLOR": "navy",
          "FOOTER_FONT_WEIGHT": "600",
          "FOOTER_TEXT_COLOR": "#737690",
          "HEADER_BACKGROUND_COLOR": "navy",
          "HEADER_TEXT_COLOR": "#FFF",
          "KAFKA_HOST": "",
          "KAFKA_PARTITION": "",
          "KAFKA_PORT": "",
          "KAFKA_TOPIC": "",
          "KEYFILE": "certs/server.key",
          "KEYS_PATH": "amfdata/keys",
          "KNOWNHOSTKEY_PARAM": "[]",
          "MADownloadButton": "True",
          "MQ_QUEUE_NAME": "registrations.message",
          "MQ_SYSMGR_QUEUE": "registrations.message",
          "MessageActivityPageSize": "50",
          "ONBOARD_COMM_CREATE_CD_PROFILE": "CREATE_CD_PROFILE",
          "ONBOARD_COMM_CREATE_SFTP_PROFILE": "CREATE_SFTP_PROFILE",
          "ONBOARD_COMM_DELETE_CD_PROFILE": "DELETE_CD_PROFILE",
          "ONBOARD_COMM_DELETE_SFTP_PROFILE": "DELETE_SFTP_PROFILE",
          "ONBOARD_COMM_UPDATE_CD_PROFILE": "UPDATE_CD_PROFILE",
          "ONBOARD_COMM_UPDATE_SFTP_PROFILE": "UPDATE_SFTP_PROFILE",
          "ONBOARD_USER_GM_DELETE_MESSAGE_TYPE": "DELETE_GM_USER",
          "ONBOARD_USER_GM_MESSAGE_TYPE": "CREATE_GM_USER",
          "ONBOARD_USER_GM_UPDATE_MESSAGE_TYPE": "UPDATE_GM_USER",
          "ONBOARD_USER_RECEIVER": "AMF_USER",
          "ONBOARD_USER_SENDER": "AMF_USER",
          "ONBOARD_USER_TM_DELETE_MESSAGE_TYPE": "DELETE_TM_USER",
          "ONBOARD_USER_TM_MESSAGE_TYPE": "CREATE_TM_USER",
          "ONBOARD_USER_TM_UPDATE_MESSAGE_TYPE": "UPDATE_TM_USER",
          "Organization": "MFTLABS",
          "PROXY_PASSWORD": "6qAhhYzOZR-82m6fufK0Y4HJ8x0mvAVi7jSp5fzIAEQ",
          "PROXY_URL": "http://localhost:58443",
          "PROXY_USERNAME": "admin",
          "SFG_API_BASE_URL": "",
          "SFG_API_BASE_URL_LIST": "",
          "SFG_API_PASSWORD": "",
          "SFG_API_USERNAME": "",
          "SFG_BASE_URL": "",
          "SFG_WORKFLOW_API": "",
          "SFTP_OUTBOUND_PRIVATE_KEYID": "",
          "STORAGE_ROOT": "amfdata",
          "SVC_API_LIST": "https://localhost:46443/amf",
          "ShowImportNavIcon": "true",
          "TIMEZONE": "Africa/Johannesburg",
          "TLSV1": "TLS_RSA_WITH_AES_256_CBC_SHA",
          "TLSV11": "TLS_RSA_WITH_AES_256_CBC_SHA",
          "TLSV12": "TLS_RSA_WITH_AES_256_CBC_SHA256",
          "DATA_LOAD_LIST": "[{\"name\":\"Banking\",\"description\":\"banking scenario\"},{\"name\":\"Retail\",\"description\":\"retail  scenario\"},{\"name\":\"Logistics\",\"description\":\"logistics  scenario\"},{\"name\":\"Health Care\",\"description\":\"health care  scenario\"}]",
          "UFA_DOWNLOAD_URL": "https://localhost:48443/amf/ufa-download",
          "UFA_VERSIONS": "3.0",
          "USER_AUTH_TYPE": "Local",
          "USE_SFTPD": "True",
          "UseGlobalMailbox": "False",
          "VERSION_NUMBER": "v25.06.01",
          "disable_contextmenu": "oncontextmenu=\"return false;\"",
          "elk_dashboard_url": "",
          "mq_channel": "nats://localhost:4222",
          "mq_host": "localhost",
          "mq_port": "4222",
          "mq_qm": "nats2",
          "mq_cluster": "{\"config_name\": \"DC01\",\"mq_channel\": \"nats://localhost:4222\",\"mq_host\": \"localhost\",\"mq_port\":\"4222\",\"mq_qm\": \"nats2\"}",
          "SCHEDULER_QUEUE": "scheduler.message"
        }',
        '{
          "created_by": "CMD",
          "created_on": "2022-01-01 11:49:42.116985",
          "last_modified_by": "",
          "last_modified_on": ""
        }');

alter table amf_ufagent_downloads add ufa_type text not null default 'Internal';

CREATE TABLE amf_meta_data (
                               meta_id UUID NOT NULL,
                               message_id UUID NOT NULL,
                               meta_data JSONB NOT NULL,
                               checksum TEXT,
                               CONSTRAINT "primary_amf_meta_data" PRIMARY KEY (meta_id, message_id)
);

alter table amf_delivery add column file_size integer not null default 0;
INSERT INTO amf_queue_definitions(queue_id,queue_name,description,queue_type,queue_manager,username,
                                  password,channel,host,port,priority,fifo,warndepth,maxdepth,user_audit_info,active) values(
                                                                                                                                '6992a55d-b8f3-41f0-9176-a08ad0b63412','workflow.message','Main workflow queue','NATS','NATS','','','NATS','localhost','4222',false,
                                                                                                                                false,false,false,'{"created_by": "CMD", "created_on": "2021-01-01 00:00:01.000", "last_modified_by": "", "last_modified_on": ""}',true);
                                                                                                                                                