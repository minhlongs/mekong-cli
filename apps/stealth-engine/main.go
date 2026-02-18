package main

import (
	"context"
	"log"
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"

	utls "github.com/refraction-networking/utls"
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	// 1. Target: Google Gemini (via OpenAI Compat)
	targetURL, _ := url.Parse("https://generativelanguage.googleapis.com")
	proxy := httputil.NewSingleHostReverseProxy(targetURL)

	// 2. Transport (Stealth Mode with uTLS)
	proxy.Transport = &http.Transport{
		DialTLSContext: func(ctx context.Context, network, addr string) (net.Conn, error) {
			// Connect to the target
			conn, err := net.Dial(network, addr)
			if err != nil {
				return nil, err
			}

			// Wrap with uTLS
			uConn := utls.UClient(conn, &utls.Config{
				ServerName: targetURL.Host,
			}, utls.HelloChrome_Auto) // Mimic Chrome

			if err := uConn.Handshake(); err != nil {
				return nil, err
			}

			return uConn, nil
		},
	}

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		// SecOps: Strip Identity Headers
		r.Header.Del("X-Forwarded-For")
		r.Header.Del("cf-connecting-ip")
		r.Host = targetURL.Host

		// WATERFALL LOGIC CAPTURE
		// We wrap the response writer to capture stats
		ww := &responseWrapper{ResponseWriter: w, statusCode: 200}
		
		log.Printf("🚀 [Stealth] Proxying request to %s (Covert: Chrome)", r.URL.Path)
		proxy.ServeHTTP(ww, r)

		// ANALYZE RESULT
		if ww.statusCode == 403 || ww.statusCode == 429 {
			log.Printf("⚠️ [WAF Trap] Blocked with %d. Reporting to Brain...", ww.statusCode)
			go reportBurnedIPToBrain("datacenter-node-01", ww.statusCode) // Mock IP for MVP
		}
	})

	log.Printf("🚀 [CoreOps] Stealth Engine is running on :%s", port)
	http.ListenAndServe(":"+port, nil)
}

// Stats Wrapper
type responseWrapper struct {
	http.ResponseWriter
	statusCode int
}

func (rw *responseWrapper) WriteHeader(code int) {
	rw.statusCode = code
	rw.ResponseWriter.WriteHeader(code)
}

// Brain Uplink
func reportBurnedIPToBrain(ip string, code int) {
	// In Prod: Call http://localhost:8000/internal/webhook/report-error
	// For MVP: Log only to avoid crashing if Brain is offline
	log.Printf("🔥 [Uplink] Sending Report: IP=%s Code=%d", ip, code)
}
