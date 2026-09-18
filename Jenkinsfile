library 'com.optum.jenkins.pipeline.library.ghec@master'
pipeline {
    agent any
    environment {
        GITHUB_ORG = 'uhg-internal'
        GITHUB_REPO = 'ppkg-claims-dark-mode-validator'
        HOSTED_APP = 'ppkg-claims-dark-mode-validator'
        GIT_TAG_PREFIX = 'v'
        ASK_ID = 'AIDE_0074753'
        APP_ID = 'ppkg-claims-dark-mode-validator'
        APP_NAME = "${GITHUB_REPO}"
        JAVA_VERSION = "11.0"
    }
    parameters {
        choice(name: 'KARATE_ENV', choices: ['nonprod','preprod', 'prod'], description: 'Pick Environment')
        string(name: 'KARATE_TAGS', description: 'Tags (comma separated, no spaces) to run, e.g. @smoke,@regression', defaultValue: '@compare-ccv1-productapi,@compare-ccv1-productapi-cosmos,@compare-ccv1-productapi-nice')
    }
    options {
        disableConcurrentBuilds()
        skipStagesAfterUnstable()
        buildDiscarder(logRotator(numToKeepStr: '10', artifactNumToKeepStr: '2'))
    }
    stages {
        stage('Compile') {
            steps {
                command '''
                        mvn clean compile
                    '''
            }
        }
        stage("Test") {
            when { branch 'master' }
            steps {
                withCredentials([
                        usernamePassword(credentialsId: "gateway-api-oauth2-credentials-nonprod",
                            passwordVariable: 'gateway_oauth_client_secret_nonprod', usernameVariable: 'gateway_oauth_client_id_nonprod'),
                        usernamePassword(credentialsId: "gateway-api-oauth2-credentials-prod",
                            passwordVariable: 'gateway_oauth_client_secret_prod', usernameVariable: 'gateway_oauth_client_id_prod'),
                         usernamePassword(credentialsId: "konga-oauth2-credentials-nonprod",
                            passwordVariable: 'konga_oauth_client_secret_nonprod', usernameVariable: 'konga_oauth_client_id_nonprod'),
                         usernamePassword(credentialsId: "konga-oauth2-credentials-prod",
                            passwordVariable: 'konga_oauth_client_secret_prod', usernameVariable: 'konga_oauth_client_id_prod')]) {
                    command '''
                        mvn clean test -Dkarate.env=${KARATE_ENV} "-Dkarate.options=--tags ${KARATE_TAGS}" -Dgateway_oauth_client_id_nonprod=$gateway_oauth_client_id_nonprod -Dgateway_oauth_client_secret_nonprod=$gateway_oauth_client_secret_nonprod  -Dgateway_oauth_client_id_prod=$gateway_oauth_client_id_prod -Dgateway_oauth_client_secret_prod=$gateway_oauth_client_secret_prod -Dkonga_oauth_client_id_nonprod=$konga_oauth_client_id_nonprod -Dkonga_oauth_client_secret_nonprod=$konga_oauth_client_secret_nonprod  -Dkonga_oauth_client_id_prod=$konga_oauth_client_id_prod -Dkonga_oauth_client_secret_prod=$konga_oauth_client_secret_prod
                    '''
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts allowEmptyArchive: true, artifacts: 'target/*comparison-report*.xlsx'
            publishHTML target: [reportName           : 'Test',
                                 reportDir            : 'target/karate-reports',
                                 reportFiles          : 'karate-summary.html',
                                 reportTitles         : 'HTML Report',
                                 keepAll              : true,
                                 alwaysLinkToLastBuild: true,
                                 allowMissing         : true]
        }
    }
}
