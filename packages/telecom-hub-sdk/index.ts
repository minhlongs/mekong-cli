/**
 * @agencyos/telecom-hub-sdk — Unified Telecom Hub
 *
 * Facade consolidating network infrastructure management, IoT device fleets,
 * subscriber lifecycle, and usage-based billing for telecom operators.
 *
 * Quick Start:
 *   import { createNetworkManager, createSubscriberManager } from '@agencyos/telecom-hub-sdk';
 *
 * Sub-path imports:
 *   import { createNetworkManager } from '@agencyos/telecom-hub-sdk/network';
 *   import { createIoTHub } from '@agencyos/telecom-hub-sdk/iot';
 *   import { createSubscriberManager } from '@agencyos/telecom-hub-sdk/subscriber';
 */

export { createNetworkManager, createCoverageAnalyzer } from './network-facade';
export { createIoTHub, createDeviceProvisioner } from './iot-facade';
export { createSubscriberManager, createUsageBilling } from './subscriber-facade';
