class Mekong < Formula
  desc "Mekong CLI - AI-operated business platform"
  homepage "https://mekong.ai"
  url "https://github.com/mekong-cli/mekong-cli/releases/download/v#{version}/mekong-#{version}-macos-arm64.tar.gz"
  version "6.0.0"
  license "MIT"

  def install
    bin.install "mekong"
  end

  test do
    system "#{bin}/mekong", "--version"
  end
end
