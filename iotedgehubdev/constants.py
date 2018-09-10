# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


class EdgeConstants():
    HOSTNAME_KEY = 'HostName'
    DEVICE_ID_KEY = 'DeviceId'
    ACCESS_KEY_KEY = 'SharedAccessKey'

    SUBJECT_COUNTRY_KEY = 'countryCode'
    SUBJECT_STATE_KEY = 'state'
    SUBJECT_LOCALITY_KEY = 'locality'
    SUBJECT_ORGANIZATION_KEY = 'organization'
    SUBJECT_ORGANIZATION_UNIT_KEY = 'organizationUnit'
    SUBJECT_COMMON_NAME_KEY = 'commonName'

    EDGE_CHAIN_CA = 'edge-chain-ca'
    EDGE_HUB_SERVER = 'edge-hub-server'
    EDGE_DEVICE_CA = 'edge-device-ca'
    EDGE_AGENT_CA = 'edge-agent-ca'
    CERT_SUFFIX = '.cert.pem'
    PFX_SUFFIX = '.cert.pfx'

    CERT_DEFAULT_DICT = {
        SUBJECT_COUNTRY_KEY: 'US',
        SUBJECT_STATE_KEY: 'Washington',
        SUBJECT_LOCALITY_KEY: 'Redmond',
        SUBJECT_ORGANIZATION_KEY: 'Default Edge Organization',
        SUBJECT_ORGANIZATION_UNIT_KEY: 'Edge Unit',
        SUBJECT_COMMON_NAME_KEY: 'Edge Test Device CA'
    }
