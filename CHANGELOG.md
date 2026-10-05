Changelog
=========

Unreleased
----------

 * Time out requests to id.scene.org after `SCENEID_TIMEOUT` seconds (default 5)
 * Handle a cancelled login, an expired session, a missing code, and errors or invalid responses from SceneID: the user is sent to `LOGIN_URL` with a message instead of getting a server error
 * A mismatched `state` now also returns to the login page with a message, instead of a 400 error
 * Each `state` is used for one login only
 * Import `urllib.parse` explicitly
 * New `SCENEID_SCOPES` setting to request scopes such as `user:email`


0.1.2 (2024-04-12)

 * Confirm Django 5.x support and remove upper bound on Django dependency


0.1.1 (2022-07-13)
------------------

 * Confirm Django 4.x support
 * Fix Django 3.0 and 3.1 compatibility by providing a default_app_config setting


0.1 (2021-05-08)
----------------

* Initial release
