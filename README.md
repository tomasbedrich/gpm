# GPM - Git Package Manager

GPM (GIT Package Manager) is a Home Assistant [integration](https://www.home-assistant.io/docs/glossary/#custom-integration) that provides an intuitive interface for managing custom_components and [dashboard](https://www.home-assistant.io/dashboards) resources directly from GIT repositories.

## Features

- **Manage custom integrations**: Easily install, update, and maintain Home Assistant custom_components from GIT repositories.
- **Simplify dashboard customization**: Download and update custom cards, themes, and other frontend resources with minimal effort.
- **Lightweight and flexible**: Works with any GIT repository and avoids dependencies on third-party APIs.

## Installation

To install GPM, run the following command:

```bash
wget -O - https://raw.githubusercontent.com/tomasbedrich/gpm/refs/heads/main/install/install.sh | bash -
```

Once installed, restart your Home Assistant instance.


## Managing packages with GPM

1. Go to **Settings** -> **Devices & Services** -> **Integrations**.
2. For each package you want to manage with GPM, click **+ Add Integration**, select **GPM**, and complete the on-screen form.


### Installing custom integrations

Custom integrations (known as custom_components) extend Home Assistant’s capabilities. These integrations reside in the `custom_components` folder within the Home Assistant configuration directory.

To install a custom integration with GPM:

1. Obtain the HTTP URL of the GIT repository containing the integration.
2. Add the repository URL in GPM’s configuration flow.
3. GPM will [clone](https://git-scm.com/docs/git-clone) the latest version of the repository and set up the required symlinks.
4. GPM automatically creates an [update entity](https://www.home-assistant.io/integrations/update/) to notify you about updates.

### Installing dashboard resources

Dashboard resources enhance the Home Assistant frontend with custom cards, themes, and more. These resources are stored in the `www` directory within the Home Assistant configuration folder.

To install dashboard resources with GPM:

1. Provide the download URL for the resource file in GPM’s configuration flow.
2. Use `{{ version }}` as a placeholder in the URL for dynamic version updates. GPM replaces this placeholder with the corresponding tag or commit hash during updates.

**Example URL:**

For a GitHub repository that publishes builds as releases:

```
https://github.com/example-user/awesome-card/releases/download/{{ version }}/awesome-card.js
```

#### Why configure download URLs manually?

Many frontend resources are distributed as pre-built artifacts (e.g., JavaScript bundles), which are not typically stored directly in GIT repositories. By manually specifying the download URL, you maintain flexibility to use resources from any GIT remote (e.g., GitHub, GitLab, etc.) without relying on specific repository structures or APIs.


## GPM vs HACS

[HACS](https://hacs.xyz/) is popular alternative to GPM for managing custom components and dashboard resources. Here’s how GPM compares:

### Similarities

- Both manage custom_components and dashboard resources.
- Both require repositories to follow [the HACS repository structure](https://hacs.xyz/docs/publish/integration/).
- Updates are triggered by publishing new tags or commits.

### Advantages of GPM

- **No GitHub account needed**: Install from any GIT repository using an HTTP URL.
- **No third-party API reliance**: GPM operates purely with GIT commands, avoiding external dependencies like release notes or pre-built bundles.
- **Lightweight and flexible**: Ideal for advanced users who value simplicity and customization.

### Advantages of HACS

- Richer feature set, including repository store, AppDaemon support, etc.
- Easier for beginners to get started with.

Summary: GPM is a lightweight alternative for advanced users who prefer flexibility over additional features.
