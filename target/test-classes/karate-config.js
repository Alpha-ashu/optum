function fn() {
    var env = karate.properties['karate.env'] || 'prod';
    karate.log('Start karate-config.js');
    karate.log('karate.env system property is:', env);

    var config = {
        env: env,
        baseUrl: 'http://localhost:' + karate.properties['port'],
        ssl: true,

        // UPM API Service
        upm_cr_prod: karate.properties['upm_gateway_oauth_client_id_prod'],
        upm_cs_prod: karate.properties['upm_gateway_oauth_client_secret_prod'],
        upm_cr_nonprod: karate.properties['upm_gateway_oauth_client_id_nonprod'],
        upm_cs_nonprod: karate.properties['upm_gateway_oauth_client_secret_nonprod'],
        upm_token_url_prod: 'https://api.uhg.com/oauth2/token',
        upm_token_url_nonprod: 'https://api-stg.uhg.com/oauth2/token',

        //UPM COB API Service Mainframe
        upm_cob_cr_prod: (karate.properties['upm_cob_gateway_oauth_client_id_prod'] || '').replace(/"/g, ''),
        upm_cob_cs_prod: (karate.properties['upm_cob_gateway_oauth_client_secret_prod'] || '').replace(/"/g, ''),
        upm_cob_cr_nonprod: (karate.properties['upm_cob_gateway_oauth_client_id_nonprod'] || '').replace(/"/g, ''),
        upm_cob_cs_nonprod: (karate.properties['upm_cob_gateway_oauth_client_secret_nonprod'] || '').replace(/"/g, ''),
        upm_cob_token_url_prod: 'https://gateway-core.optum.com/auth/oauth2/cached/token',
        upm_cob_token_url_nonprod: 'https://api-stg.uhg.com/oauth2/token',

        // PPKG API Service
        ppkg_cr_prod: karate.properties['ppkg_gateway_oauth_client_id_prod'],
        ppkg_cs_prod: karate.properties['ppkg_gateway_oauth_client_secret_prod'],
        ppkg_cr_nonprod: karate.properties['ppkg_gateway_oauth_client_id_nonprod'],
        ppkg_cs_nonprod: karate.properties['ppkg_gateway_oauth_client_secret_nonprod'],
        ppkg_token_url_prod: 'https://api.uhg.com/oauth2/token',
        ppkg_token_url_nonprod: 'https://api-stg.uhg.com/oauth2/token',

        // ALEX API Service
        alex_cr_prod: karate.properties['alex_gateway_oauth_client_id_prod'],
        alex_cs_prod: karate.properties['alex_gateway_oauth_client_secret_prod'],
        alex_cr_nonprod: karate.properties['alex_gateway_oauth_client_id_nonprod'],
        alex_cs_nonprod: karate.properties['alex_gateway_oauth_client_secret_nonprod'],
        alex_token_url_prod: 'https://api.uhg.com/oauth2/token',
        alex_token_url_nonprod: 'https://api-stg.uhg.com/oauth2/token',
        product_api_consumername: 'bene_public_np',
        product_api_roleid: 'bene_public_np-onshore',

        // Claim360
        claim360_cr_prod: karate.properties['claim360_gateway_oauth_client_id_prod'],
        claim360_cs_prod: karate.properties['claim360_gateway_oauth_client_secret_prod'],
        claim360_cr_nonprod: karate.properties['claim360_gateway_oauth_client_id_nonprod'],
        claim360_cs_nonprod: karate.properties['claim360_gateway_oauth_client_secret_nonprod'],
        claim360_token_url_prod: 'https://api.uhg.com/oauth2/token',
        claim360_token_url_nonprod: 'https://gateway-stage-dmz.optum.com/auth/oauth2/cached/token',

        // COB
        COB_cr_prod: karate.properties['cob_gateway_oauth_client_id_prod'],
        COB_cs_prod: karate.properties['cob_gateway_oauth_client_secret_prod'],
        COB_cr_nonprod: karate.properties['cob_gateway_oauth_client_id_nonprod'],
        COB_cs_nonprod: karate.properties['cob_gateway_oauth_client_secret_nonprod'],
        COB_token_url_prod: 'https://api.uhg.com/oauth2/token',
        COB_token_url_nonprod: 'https://api-stg.uhg.com/oauth2/token'

    };

    // UPM Prod Access Token
    if (config.upm_cr_prod && config.upm_cs_prod) {
        try {
            var upmOAuthResult = karate.callSingle('classpath:authorization_token/prod/UPM_Prod_AccessToken.feature', config);
            config.UPM_GatewayAccessToken_prod = 'Bearer ' + upmOAuthResult.response.access_token;
            karate.log('UPM API Gateway Access Token was fetched successfully.');
        } catch (e) {
            karate.log('Failed to fetch UPM API Gateway Access Token:', e.message);
        }
    } else {
        karate.log('UPM OAuth credentials not provided. Skipping token generation.');
    }

    // UPM COB Prod Access Token
    if (config.upm_cob_cr_prod && config.upm_cob_cs_prod) {
        try {
            var upmCobOAuthResult = karate.callSingle('classpath:authorization_token/prod/UPM_Cob_Prod_AccessToken.feature', config);
            config.UPM_COB_GatewayAccessToken_prod = 'Bearer ' + upmCobOAuthResult.response.access_token;
            karate.log('UPM COB Access Token was fetched successfully.');
        } catch (e) {
            karate.log('Failed to fetch UPM COB Access Token:', e.message);
        }
    } else {
        karate.log('UPM COB OAuth credentials not provided. Skipping token generation.');
    }

    // PPKG Prod Access Token
    if (config.ppkg_cr_prod && config.ppkg_cs_prod) {
        var ppkgOAuthResult = karate.callSingle('classpath:authorization_token/prod/PPKG_Prod_AccessToken.feature', config);
        config.PPKG_GatewayAccessToken_prod = 'Bearer ' + ppkgOAuthResult.response.access_token;
        karate.log('PPKG Access Token was fetched successfully.');
    } else {
        karate.log('PPKG OAuth credentials not provided. Skipping token generation.');
    }

    // ALEX Prod Access Token
    if (config.alex_cr_prod && config.alex_cs_prod) {
        var alexOAuthResult = karate.callSingle('classpath:authorization_token/prod/ALEX_Prod_AccessToken.feature', config);
        config.ALEX_GatewayAccessToken_prod = 'Bearer ' + alexOAuthResult.response.access_token;
        karate.log('ALEX Access Token was fetched successfully.');
    } else {
        karate.log('ALEX OAuth credentials not provided. Skipping token generation.');
    }

    // Claim360 Prod Access Token
    if (config.claim360_cr_prod && config.claim360_cs_prod) {
        try {
            var claim360OAuthResult = karate.callSingle('classpath:authorization_token/prod/Claim360_Prod_AccessToken.feature', config);
            config.Claim360_GatewayAccessToken_prod = 'Bearer ' + claim360OAuthResult.response.access_token;
            karate.log('Claim360 Access Token was fetched successfully.');
        } catch (e) {
            karate.log('Failed to fetch Claim360 Access Token:', e.message);
        }
    } else {
        karate.log('Claim360 OAuth credentials not provided. Skipping token generation.');
    }

    // COB Prod Access Token
    if (config.COB_cr_prod && config.COB_cs_prod) {
        try {
            var cobOAuthResult = karate.callSingle('classpath:authorization_token/prod/COB_Prod_AccessToken.feature', config);
            config.COB_GatewayAccessToken_prod = 'Bearer ' + cobOAuthResult.response.access_token;
            karate.log('COB Access Token was fetched successfully.');
        } catch (e) {
            karate.log('Failed to fetch COB Access Token:', e.message);
        }
    } else {
        karate.log('COB OAuth credentials not provided. Skipping token generation.');
    }

    // UPM Non-Prod Access Token
    if (config.upm_cr_nonprod && config.upm_cs_nonprod) {
        try {
            var upmOAuthResultNonProd = karate.callSingle('classpath:authorization_token/nonprod/UPM_NonProd_AccessToken.feature', config);
            config.UPM_GatewayAccessToken_nonprod = 'Bearer ' + upmOAuthResultNonProd.response.access_token;
            karate.log('UPM API Gateway Access Token (Non-Prod) was fetched successfully.');
        } catch (e) {
            karate.log('Failed to fetch UPM API Gateway Access Token (Non-Prod):', e.message);
        }
    } else {
        karate.log('UPM OAuth credentials (Non-Prod) not provided. Skipping token generation.');
    }

    // PPKG Non-Prod Access Token
    if (config.ppkg_cr_nonprod && config.ppkg_cs_nonprod) {
        try {
            var ppkgOAuthResultNonProd = karate.callSingle('classpath:authorization_token/nonprod/PPKG_NonProd_AccessToken.feature', config);
            config.PPKG_GatewayAccessToken_nonprod = 'Bearer ' + ppkgOAuthResultNonProd.response.access_token;
            karate.log('PPKG Access Token (Non-Prod) was fetched successfully.');
        } catch (e) {
            karate.log('Failed to fetch PPKG Access Token (Non-Prod):', e.message);
        }
    } else {
        karate.log('PPKG OAuth credentials (Non-Prod) not provided. Skipping token generation.');
    }

    // ALEX Non-Prod Access Token
    if (config.alex_cr_nonprod && config.alex_cs_nonprod) {
        try {
            var alexOAuthResultNonProd = karate.callSingle('classpath:authorization_token/nonprod/ALEX_NonProd_AccessToken.feature', config);
            config.ALEX_GatewayAccessToken_nonprod = 'Bearer ' + alexOAuthResultNonProd.response.access_token;
            karate.log('ALEX Access Token (Non-Prod) was fetched successfully.');
        } catch (e) {
            karate.log('Failed to fetch ALEX Access Token (Non-Prod):', e.message);
        }
    } else {
        karate.log('ALEX OAuth credentials (Non-Prod) not provided. Skipping token generation.');
    }

    // Claim360 Non-Prod Access Token
    if (config.claim360_cr_nonprod && config.claim360_cs_nonprod) {
        try {
            var claim360OAuthResultNonProd = karate.callSingle('classpath:authorization_token/nonprod/Claim360_NonProd_AccessToken.feature', config);
            config.Claim360_GatewayAccessToken_nonprod = 'Bearer ' + claim360OAuthResultNonProd.response.access_token;
            karate.log('Claim360 Access Token (Non-Prod) was fetched successfully.');
        } catch (e) {
            karate.log('Failed to fetch Claim360 Access Token (Non-Prod):', e.message);
        }
    } else {
        karate.log('Claim360 OAuth credentials (Non-Prod) not provided. Skipping token generation.');
    }

    // COB Non-Prod Access Token
    if (config.COB_cr_nonprod && config.COB_cs_nonprod) {
        try {
            var cobOAuthResultNonProd = karate.callSingle('classpath:authorization_token/nonprod/COB_NonProd_AccessToken.feature', config);
            config.COB_GatewayAccessToken_nonprod = 'Bearer ' + cobOAuthResultNonProd.response.access_token;
            karate.log('COB Access Token (Non-Prod) was fetched successfully.');
        } catch (e) {
            karate.log('Failed to fetch COB Access Token (Non-Prod):', e.message);
        }
    } else {
        karate.log('COB OAuth credentials (Non-Prod) not provided. Skipping token generation.');
    }

    // Environment-specific overrides
    if (env === 'local') {
        config.gateway_api_url = 'http://localhost:8080';
        config.gateway_core_url = 'https://gateway-stage-core.optum.com';
        config.oauth_token_url = 'https://gateway-stage-core.optum.com/auth/oauth2/token';
        config.product_api_gateway_api_url = 'https://api-stg.uhg.com';
        config.gateway_x_upstream_env = "stage";
    } else if (env === 'prod') {
        config.gateway_api_url = 'https://api.uhg.com';
        config.gateway_core_url = 'https://gateway-core.optum.com';
        config.oauth_token_url = 'https://gateway-core.optum.com/auth/oauth2/token';
        config.UPM_GatewayAccessToken = config.UPM_GatewayAccessToken_prod;
        config.UPM_COB_GatewayAccessToken = config.UPM_COB_GatewayAccessToken_prod;
        config.PPKG_GatewayAccessToken = config.PPKG_GatewayAccessToken_prod;
        config.ALEX_GatewayAccessToken = config.ALEX_GatewayAccessToken_prod;
        config.Claim360_GatewayAccessToken = config.Claim360_GatewayAccessToken_prod;
        config.COB_GatewayAccessToken = config.COB_GatewayAccessToken_prod;
        config.gateway_x_upstream_env = "prod";
        config.product_api_consumername = 'bene_public_prd';
        config.product_api_roleid = 'bene_public_prd-onshore';
    } else if (env === 'nonprod') {
        config.gateway_api_url = 'https://api-stg.uhg.com';
        config.gateway_core_url = 'https://gateway-stage-core.optum.com';
        config.oauth_token_url = 'https://api-stg.uhg.com/oauth2/token';
        config.UPM_GatewayAccessToken = config.UPM_GatewayAccessToken_nonprod;
        config.PPKG_GatewayAccessToken = config.PPKG_GatewayAccessToken_nonprod;
        config.ALEX_GatewayAccessToken = config.ALEX_GatewayAccessToken_nonprod;
        config.Claim360_GatewayAccessToken = config.Claim360_GatewayAccessToken_nonprod;
        config.COB_GatewayAccessToken = config.COB_GatewayAccessToken_nonprod;
        config.gateway_x_upstream_env = "nonprod";
        config.product_api_consumername = 'bene_public_prd';
        config.product_api_roleid = 'bene_public_prd-onshore';
    }

    karate.configure('ssl', true);

    // Register a JVM shutdown hook ONCE to auto-generate Performance Excel report
    if (!karate.properties['__perfHookRegistered']) {
        var shutdownHook = new java.lang.Thread(function() {
            var csvFile = new java.io.File('target/Performance/performance_log.csv');
            if (csvFile.exists() && csvFile.length() > 0) {
                try {
                    var pb = new java.lang.ProcessBuilder(['python', 'src/test/utility/performance/generate_performance_report.py']);
                    pb.inheritIO();
                    var proc = pb.start();
                    proc.waitFor();
                } catch(e) { /* ignore */ }
            }
        });
        shutdownHook.setName('perf-report-generator');
        java.lang.Runtime.getRuntime().addShutdownHook(shutdownHook);
        java.lang.System.setProperty('__perfHookRegistered', 'true');
    }

    karate.log('End karate-config.js');
    return config;
}