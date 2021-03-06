from __future__ import unicode_literals
import boto
import sure  # noqa

from nose.tools import assert_raises, assert_equals, assert_not_equals
from boto.exception import BotoServerError
import base64
from moto import mock_iam
from nose.tools import raises


@mock_iam()
def test_get_all_server_certs():
    conn = boto.connect_iam()

    conn.upload_server_cert("certname", "certbody", "privatekey")
    certs = conn.get_all_server_certs()['list_server_certificates_response']['list_server_certificates_result']['server_certificate_metadata_list']
    certs.should.have.length_of(1)
    cert1 = certs[0]
    cert1.server_certificate_name.should.equal("certname")
    cert1.arn.should.equal("arn:aws:iam::123456789012:server-certificate/certname")


@mock_iam()
def test_get_server_cert():
    conn = boto.connect_iam()

    conn.upload_server_cert("certname", "certbody", "privatekey")
    cert = conn.get_server_certificate("certname")
    cert.server_certificate_name.should.equal("certname")
    cert.arn.should.equal("arn:aws:iam::123456789012:server-certificate/certname")


@mock_iam()
def test_upload_server_cert():
    conn = boto.connect_iam()

    conn.upload_server_cert("certname", "certbody", "privatekey")
    cert = conn.get_server_certificate("certname")
    cert.server_certificate_name.should.equal("certname")
    cert.arn.should.equal("arn:aws:iam::123456789012:server-certificate/certname")


@mock_iam()
@raises(BotoServerError)
def test_get_role__should_throw__when_role_does_not_exist():
    conn = boto.connect_iam()

    conn.get_role('unexisting_role')


@mock_iam()
def test_create_role_and_instance_profile():
    conn = boto.connect_iam()
    conn.create_instance_profile("my-profile", path="my-path")
    conn.create_role("my-role", assume_role_policy_document="some policy", path="my-path")

    conn.add_role_to_instance_profile("my-profile", "my-role")

    role = conn.get_role("my-role")
    role.path.should.equal("my-path")
    role.assume_role_policy_document.should.equal("some policy")

    profile = conn.get_instance_profile("my-profile")
    profile.path.should.equal("my-path")
    role_from_profile = list(profile.roles.values())[0]
    role_from_profile['role_id'].should.equal(role.role_id)
    role_from_profile['role_name'].should.equal("my-role")

    conn.list_roles().roles[0].role_name.should.equal('my-role')


@mock_iam()
def test_remove_role_from_instance_profile():
    conn = boto.connect_iam()
    conn.create_instance_profile("my-profile", path="my-path")
    conn.create_role("my-role", assume_role_policy_document="some policy", path="my-path")
    conn.add_role_to_instance_profile("my-profile", "my-role")

    profile = conn.get_instance_profile("my-profile")
    role_from_profile = list(profile.roles.values())[0]
    role_from_profile['role_name'].should.equal("my-role")

    conn.remove_role_from_instance_profile("my-profile", "my-role")

    profile = conn.get_instance_profile("my-profile")
    dict(profile.roles).should.be.empty


@mock_iam()
def test_list_instance_profiles():
    conn = boto.connect_iam()
    conn.create_instance_profile("my-profile", path="my-path")
    conn.create_role("my-role", path="my-path")

    conn.add_role_to_instance_profile("my-profile", "my-role")

    profiles = conn.list_instance_profiles().instance_profiles

    len(profiles).should.equal(1)
    profiles[0].instance_profile_name.should.equal("my-profile")
    profiles[0].roles.role_name.should.equal("my-role")


@mock_iam()
def test_list_instance_profiles_for_role():
    conn = boto.connect_iam()

    conn.create_role(role_name="my-role", assume_role_policy_document="some policy", path="my-path")
    conn.create_role(role_name="my-role2", assume_role_policy_document="some policy2", path="my-path2")

    profile_name_list = ['my-profile', 'my-profile2']
    profile_path_list = ['my-path', 'my-path2']
    for profile_count in range(0, 2):
        conn.create_instance_profile(profile_name_list[profile_count], path=profile_path_list[profile_count])

    for profile_count in range(0, 2):
        conn.add_role_to_instance_profile(profile_name_list[profile_count], "my-role")

    profile_dump = conn.list_instance_profiles_for_role(role_name="my-role")
    profile_list = profile_dump['list_instance_profiles_for_role_response']['list_instance_profiles_for_role_result']['instance_profiles']
    for profile_count in range(0, len(profile_list)):
        profile_name_list.remove(profile_list[profile_count]["instance_profile_name"])
        profile_path_list.remove(profile_list[profile_count]["path"])
        profile_list[profile_count]["roles"]["member"]["role_name"].should.equal("my-role")

    len(profile_name_list).should.equal(0)
    len(profile_path_list).should.equal(0)

    profile_dump2 = conn.list_instance_profiles_for_role(role_name="my-role2")
    profile_list = profile_dump2['list_instance_profiles_for_role_response']['list_instance_profiles_for_role_result']['instance_profiles']
    len(profile_list).should.equal(0)


@mock_iam()
def test_list_role_policies():
    conn = boto.connect_iam()
    conn.create_role("my-role")
    conn.put_role_policy("my-role", "test policy", "my policy")
    role = conn.list_role_policies("my-role")
    role.policy_names[0].should.equal("test policy")


@mock_iam()
def test_put_role_policy():
    conn = boto.connect_iam()
    conn.create_role("my-role", assume_role_policy_document="some policy", path="my-path")
    conn.put_role_policy("my-role", "test policy", "my policy")
    policy = conn.get_role_policy("my-role", "test policy")['get_role_policy_response']['get_role_policy_result']['policy_name']
    policy.should.equal("test policy")


@mock_iam()
def test_update_assume_role_policy():
    conn = boto.connect_iam()
    role = conn.create_role("my-role")
    conn.update_assume_role_policy(role.role_name, "my-policy")
    role = conn.get_role("my-role")
    role.assume_role_policy_document.should.equal("my-policy")


@mock_iam()
def test_create_user():
    conn = boto.connect_iam()
    conn.create_user('my-user')
    with assert_raises(BotoServerError):
        conn.create_user('my-user')


@mock_iam()
def test_get_user():
    conn = boto.connect_iam()
    with assert_raises(BotoServerError):
        conn.get_user('my-user')
    conn.create_user('my-user')
    conn.get_user('my-user')


@mock_iam()
def test_create_login_profile():
    conn = boto.connect_iam()
    with assert_raises(BotoServerError):
        conn.create_login_profile('my-user', 'my-pass')
    conn.create_user('my-user')
    conn.create_login_profile('my-user', 'my-pass')
    with assert_raises(BotoServerError):
        conn.create_login_profile('my-user', 'my-pass')


@mock_iam()
def test_create_access_key():
    conn = boto.connect_iam()
    with assert_raises(BotoServerError):
        conn.create_access_key('my-user')
    conn.create_user('my-user')
    conn.create_access_key('my-user')


@mock_iam()
def test_get_all_access_keys():
    conn = boto.connect_iam()
    conn.create_user('my-user')
    response = conn.get_all_access_keys('my-user')
    assert_equals(
        response['list_access_keys_response']['list_access_keys_result']['access_key_metadata'],
        []
    )
    conn.create_access_key('my-user')
    response = conn.get_all_access_keys('my-user')
    assert_not_equals(
        response['list_access_keys_response']['list_access_keys_result']['access_key_metadata'],
        []
    )


@mock_iam()
def test_delete_access_key():
    conn = boto.connect_iam()
    conn.create_user('my-user')
    access_key_id = conn.create_access_key('my-user')['create_access_key_response']['create_access_key_result']['access_key']['access_key_id']
    conn.delete_access_key(access_key_id, 'my-user')


@mock_iam()
def test_delete_user():
    conn = boto.connect_iam()
    with assert_raises(BotoServerError):
        conn.delete_user('my-user')
    conn.create_user('my-user')
    conn.delete_user('my-user')


@mock_iam()
def test_generate_credential_report():
    conn = boto.connect_iam()
    result = conn.generate_credential_report()
    result['generate_credential_report_response']['generate_credential_report_result']['state'].should.equal('STARTED')
    result = conn.generate_credential_report()
    result['generate_credential_report_response']['generate_credential_report_result']['state'].should.equal('COMPLETE')


@mock_iam()
def test_get_credential_report():
    conn = boto.connect_iam()
    conn.create_user('my-user')
    with assert_raises(BotoServerError):
        conn.get_credential_report()
    result = conn.generate_credential_report()
    while result['generate_credential_report_response']['generate_credential_report_result']['state'] != 'COMPLETE':
        result = conn.generate_credential_report()
    result = conn.get_credential_report()
    report = base64.b64decode(result['get_credential_report_response']['get_credential_report_result']['content'].encode('ascii')).decode('ascii')
    report.should.match(r'.*my-user.*')
