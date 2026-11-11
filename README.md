# Void Vision Homebrew tap

Homebrew distribution tooling for Voido and Void Island.

The intended channels are **alpha for early testing** and **beta for the website download**. Each channel has its own explicit Cask token. Homebrew installs an already-built application; it does not replace building, signing or notarizing it.

## Availability

No installable Cask has been published yet. The release checks below must pass before a Cask is added. Do not treat these planned commands as available installers until the corresponding file appears in `Casks/`:

```sh
brew install --cask void-vision/tap/voido@alpha
brew install --cask void-vision/tap/void-island@alpha
```

Once installed, channel updates use Homebrew's usual `brew update` and `brew upgrade --cask` workflow. Alpha is an explicitly selected testing channel. This tap does not promise that alpha and beta can run side by side; the Casks declare channel conflicts and never delete application data.

## Preparing a release

1. Build the intended channel and version. Test it on the declared macOS version and architecture.
2. Sign with the Void Vision Developer ID, notarize, and staple the application.
3. Run `scripts/prepare-cask.py --help`. Supply the app, matching version, channel, tested minimum macOS, architecture, fixed public Release ZIP URL and a new output directory.
4. The script checks the app's identity, signature, Gatekeeper assessment, version and architecture, then produces the ZIP, SHA-256, release manifest and Cask. It refuses development/ad-hoc signing and mismatched channels.
5. Upload that exact ZIP to the product's GitHub Release. Verify its public download and checksum, then run `brew style`, `brew audit --cask` and a clean install/uninstall test in a temporary app directory.
6. Commit the Cask and push only after those checks. Keep beta links on the website separate from alpha links.

Voido releases: https://github.com/void-vision/voido/releases

Void Island releases: https://github.com/void-vision/void-island/releases

## Documentation

- [Homebrew taps](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap)
- [Cask format, app archives and checksums](https://docs.brew.sh/Cask-Cookbook)
- [Homebrew release-channel and platform policies](https://docs.brew.sh/Acceptable-Casks)
