git-ticket
==========

git-ticket is a git extension to help developers manage the issue/ticket tracking system.

git-ticket supports **github**, **bitbucket**, and **redmine**.

This tool is currentry **under development** state and not tested enough.

Installation
------------

From PyPI:

```bash
pip install gitticket
```

or github(unstable):

```bash
pip install -e git+https://github.com/aflc/git-ticket.git#egg=git-ticket
```

Usage
-----

### configuration

For github,

```bash
git config ticket.github.token <your_access_token>
```

To get your access token, try this:

```bash
git ticket github-authorize
```


For bitbucket,

```bash
git config ticket.bitbucket.token <your_access_token>
git config ticket.bitbucket.token-secret <your_access_token_secret>
```

To get your access token and access token secret, try this:

```bash
git ticket bitbucket-authorize
```


For redmine,

```bash
git config ticket.redmine.token <your_apikey>
git config ticket.redmine.url <your_redmine_root>
```

And some other settings:

```bash
git config ticket.name <your_account_name_for_a_service> # if no value, guess from user.name
git config ticket.service <service_name> # if no value, guess from origin url
git config ticket.repo <repository_name> # if no value, guess from origin url or root derectory name.
```

For Redmine service, you must set ticket.service=redmine.


### ticket list

```bash
git ticket list
```

### ticket detail

```bash
git ticket show <issue id>
```

### add ticket

```bash
git ticket add
```

### update ticket

```bash
git ticket update <issue id>
```

### comment to a ticket

```bash
git ticket comment <issue id>
```

### close ticket

```
git ticket close <issue id>
```

ReleaseNote
===========

* v0.3
: Initial release

License
=======

It is released under the MIT license.

```
    Copyright (c) 2011 Hiroyuki Tanaka
    
    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
    
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```

