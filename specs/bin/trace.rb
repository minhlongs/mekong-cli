#!/usr/bin/env ruby
# specs/bin/trace.rb — spec-kit requirement/bundle tracer
# Usage: ruby specs/bin/trace.rb init|bundle|verify

require "json"
require "fileutils"

TRACE_FILE = File.expand_path("../../traceability.json", __dir__)

def load_trace
  File.exist?(TRACE_FILE) ? JSON.parse(File.read(TRACE_FILE)) : {"requirements" => {}, "bundles" => []}
rescue JSON::ParserError
  {"requirements" => {}, "bundles" => []}
end

def save_trace(data)
  File.write(TRACE_FILE, JSON.pretty_generate(data) + "\n")
end

def cmd_init
  data = load_trace
  data["last_init"] = Time.now.utc.iso8601
  save_trace(data)
  puts "trace initialized at #{TRACE_FILE}"
end

def cmd_bundle(name, reqs)
  data = load_trace
  bundle = {"name" => name, "requirements" => reqs, "created_at" => Time.now.utc.iso8601}
  data["bundles"] << bundle
  reqs.each { |r| data["requirements"][r] ||= {"bundles" => []}; data["requirements"][r]["bundles"] << name }
  save_trace(data)
  puts "bundle '#{name}' registered with #{reqs.length} requirements"
end

def cmd_verify
  data = load_trace
  missing = data["requirements"].select { |_, v| v["bundles"].empty? }.keys
  if missing.empty?
    puts "OK: all requirements are covered by at least one bundle"
  else
    puts "FAIL: uncovered requirements: #{missing.join(", ")}"
    exit 1
  end
end

command = ARGV.shift
case command
when "init" then cmd_init
when "bundle" then cmd_bundle(ARGV.shift, ARGV)
when "verify" then cmd_verify
else
  puts "Usage: trace.rb init|bundle <name> <req...>|verify"
  exit 1
end