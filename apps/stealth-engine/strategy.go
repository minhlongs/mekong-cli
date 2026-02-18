package main

import (
	"errors"
	"net/url"
	"sync"
)

// Strategy defines how we select a proxy
type Strategy int

const (
	StrategyResidential Strategy = iota
	StrategyDatacenter
	StrategyHybrid
)

type ProxyManager struct {
	Strategy       Strategy
	ResiProxies    []*url.URL
	DCProxies      []*url.URL
	CurrentIndex   int
	mu             sync.Mutex
}

func NewProxyManager(strategy Strategy) *ProxyManager {
	return &ProxyManager{
		Strategy:    strategy,
		ResiProxies: make([]*url.URL, 0),
		DCProxies:   make([]*url.URL, 0),
	}
}

func (pm *ProxyManager) AddResidential(proxyURL string) {
	u, _ := url.Parse(proxyURL)
	pm.ResiProxies = append(pm.ResiProxies, u)
}

func (pm *ProxyManager) AddDatacenter(proxyURL string) {
	u, _ := url.Parse(proxyURL)
	pm.DCProxies = append(pm.DCProxies, u)
}

func (pm *ProxyManager) Next() (*url.URL, error) {
	pm.mu.Lock()
	defer pm.mu.Unlock()

	// HYBRID LOGIC:
	// 1. Try Datacenter first (Cost: Cheap)
	// 2. If DC fails/banned (Logic to be added), fallback to Residential (Cost: High)
	
	// For MVP Round-Robin:
	if len(pm.DCProxies) > 0 {
		p := pm.DCProxies[pm.CurrentIndex%len(pm.DCProxies)]
		pm.CurrentIndex++
		return p, nil
	}
	
	if len(pm.ResiProxies) > 0 {
		p := pm.ResiProxies[pm.CurrentIndex%len(pm.ResiProxies)]
		pm.CurrentIndex++
		return p, nil
	}

	return nil, errors.New("no proxies available")
}
