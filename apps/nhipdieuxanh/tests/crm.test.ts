import { describe, it, expect, beforeEach, afterAll } from 'vitest'
import { prisma } from '@/lib/prisma'
import { POST as postLeads } from '@/app/api/leads/route'
import { POST as postUpdateStatus } from '@/app/api/leads/update-status/route'
import { POST as postPosts } from '@/app/api/posts/route'
import { POST as postFAQQuery } from '@/app/api/faq/query/route'
import crypto from 'crypto'
import { notarizeLeadOnBlockchain } from '@/lib/blockchain'

// Generate hashes of the test phones we will use
const testPhones = ['0912345678', '0987654321', '0923456789']
const testHashes = testPhones.map(phone =>
  crypto.createHash('sha256').update(phone).digest('hex')
)

async function cleanup() {
  await prisma.lead.deleteMany({
    where: {
      OR: [
        { leadHash: { in: testHashes } },
        { name: { startsWith: 'TEST_LEAD_' } }
      ]
    }
  })
}

beforeEach(async () => {
  await cleanup()
})

afterAll(async () => {
  await cleanup()
  await prisma.$disconnect()
})

describe('Nhịp Điệu Xanh CRM Integration Tests', () => {
  describe('Lead Ingestion (POST /api/leads)', () => {
    it('should correctly ingest a HOT lead and classify persona as "Nhà đầu tư"', async () => {
      const payload = {
        name: 'TEST_LEAD_HOT',
        phone: '0912345678',
        email: 'test_lead_hot@example.com',
        need: 'Cần mua đầu tư để sinh lời',
        budget: '3 tỷ',
        area: 'Cái Răng, Cần Thơ',
        consent: true
      }

      const req = new Request('http://localhost/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const res = await postLeads(req)
      expect(res.status).toBe(201)

      const body = await res.json()
      expect(body.success).toBe(true)
      expect(body.level).toBe('hot')
      expect(body.persona).toBe('Nhà đầu tư')
      expect(body.score).toBeGreaterThanOrEqual(70)

      // Verify db state
      const dbLead = await prisma.lead.findUnique({
        where: { id: body.leadId }
      })
      expect(dbLead).not.toBeNull()
      expect(dbLead?.name).toBe('TEST_LEAD_HOT')
      expect(dbLead?.level).toBe('hot')
      expect(dbLead?.status).toBe('new')
    })

    it('should correctly ingest a WARM lead and classify persona as "Phụ huynh học sinh"', async () => {
      const payload = {
        name: 'TEST_LEAD_WARM',
        phone: '0923456789',
        email: 'test_lead_warm@example.com',
        need: 'Mua căn hộ đi học cho con',
        budget: '1 tỷ',
        area: 'Đồng Tháp',
        consent: true
      }

      const req = new Request('http://localhost/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const res = await postLeads(req)
      expect(res.status).toBe(201)

      const body = await res.json()
      expect(body.success).toBe(true)
      expect(body.level).toBe('warm')
      expect(body.persona).toBe('Phụ huynh học sinh')

      // Verify db state
      const dbLead = await prisma.lead.findUnique({
        where: { id: body.leadId }
      })
      expect(dbLead).not.toBeNull()
      expect(dbLead?.level).toBe('warm')
    })

    it('should correctly ingest a COLD lead and classify persona as "Người mua nhà định cư"', async () => {
      const payload = {
        name: 'TEST_LEAD_COLD',
        phone: '0912345678',
        email: '',
        need: 'Mua căn hộ để ở định cư lâu dài',
        budget: '1.5 tỷ',
        area: 'Hà Nội',
        consent: true
      }

      const req = new Request('http://localhost/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const res = await postLeads(req)
      expect(res.status).toBe(201)

      const body = await res.json()
      expect(body.success).toBe(true)
      expect(body.level).toBe('cold')
      expect(body.persona).toBe('Người mua nhà định cư')

      // Verify db state
      const dbLead = await prisma.lead.findUnique({
        where: { id: body.leadId }
      })
      expect(dbLead).not.toBeNull()
      expect(dbLead?.level).toBe('cold')
    })

    it('should ingest a lead, publish to Kafka, and have Python service update sentiment/persona in DB', async () => {
      const payload = {
        name: 'TEST_LEAD_KAFKA_SYNC',
        phone: '0923456789',
        email: 'kafka_test@example.com',
        need: 'Tôi cần mua nhà mặt phố đẹp để đầu tư sinh lời nhanh',
        budget: '5 tỷ',
        area: 'Quận Cái Răng, Cần Thơ',
        consent: true
      }

      const req = new Request('http://localhost/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const res = await postLeads(req)
      expect(res.status).toBe(201)

      const body = await res.json()
      expect(body.success).toBe(true)

      const leadId = body.leadId

      // Poll db state until sentiment and persona are updated by Python service (up to 6s)
      let dbLead = null
      for (let i = 0; i < 30; i++) {
        dbLead = await prisma.lead.findUnique({
          where: { id: leadId }
        })
        if (dbLead && dbLead.sentiment === 'POSITIVE' && dbLead.persona === 'Nhà đầu tư') {
          break
        }
        await new Promise(resolve => setTimeout(resolve, 200))
      }

      expect(dbLead).not.toBeNull()
      expect(dbLead?.sentiment).toBe('POSITIVE')
      expect(dbLead?.persona).toBe('Nhà đầu tư')
    })
  })

  describe('Decree 13 Masking', () => {
    it('should save lead details masked when consent is false but generate leadHash', async () => {
      const payload = {
        name: 'TEST_LEADS LEAD MASKED',
        phone: '0987654321',
        email: 'test_lead_masked@example.com',
        need: 'Cần mua nhà định cư',
        budget: '2 tỷ',
        area: 'Cần Thơ',
        consent: false
      }

      const req = new Request('http://localhost/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const res = await postLeads(req)
      expect(res.status).toBe(201)

      const body = await res.json()
      expect(body.success).toBe(true)
      expect(body.masked).toBe(true)

      // Query database directly by the returned lead ID
      const dbLead = await prisma.lead.findUnique({
        where: { id: body.leadId }
      })

      expect(dbLead).not.toBeNull()
      // Check masked name
      expect(dbLead?.name).toBe('T********* L*** M*****')
      // Check masked phone
      expect(dbLead?.phone).toBe('098*****21')
      // Check masked email
      expect(dbLead?.email).toBe('t**************d@example.com')
      // Hash should be securely generated (e.g. UUID) and not equal to phone's SHA-256 hash
      expect(dbLead?.leadHash).not.toBeNull()
      const rawPhoneHash = crypto.createHash('sha256').update('0987654321').digest('hex')
      expect(dbLead?.leadHash).not.toBe(rawPhoneHash)
    })
  })

  describe('Status Updates (POST /api/leads/update-status)', () => {
    it('should mutate lead status and write it correctly to PostgreSQL', async () => {
      // 1. Create a lead first
      const payload = {
        name: 'TEST_LEAD_HOT',
        phone: '0912345678',
        email: 'test_lead_hot@example.com',
        need: 'Mua đầu tư',
        budget: '2.5 tỷ',
        area: 'Cần Thơ',
        consent: true
      }

      const createReq = new Request('http://localhost/api/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const createRes = await postLeads(createReq)
      const createBody = await createRes.json()
      const leadId = createBody.leadId
      expect(leadId).toBeDefined()

      // 2. Update status
      const updatePayload = {
        id: leadId,
        status: 'contacted'
      }

      const updateReq = new Request('http://localhost/api/leads/update-status', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updatePayload)
      })

      const updateRes = await postUpdateStatus(updateReq)
      expect(updateRes.status).toBe(200)

      const updateBody = await updateRes.json()
      expect(updateBody.success).toBe(true)
      expect(updateBody.lead.status).toBe('contacted')

      // 3. Verify in PostgreSQL
      const dbLead = await prisma.lead.findUnique({
        where: { id: leadId }
      })
      expect(dbLead?.status).toBe('contacted')
    })
  })

  describe('AI Property Generator (POST /api/posts)', () => {
    it('should generate a social post and return text and hashtags', async () => {
      const payload = {
        propertyType: 'Căn hộ',
        area: 'Cái Răng, Cần Thơ',
        price: '2.5 tỷ',
        tone: 'chuyên nghiệp',
        length: 'ngắn'
      }

      const req = new Request('http://localhost/api/posts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const res = await postPosts(req)
      expect(res.status).toBe(200)

      const body = await res.json()
      expect(body.id).toBeDefined()
      expect(typeof body.text).toBe('string')
      expect(body.text.length).toBeGreaterThan(0)
      expect(Array.isArray(body.hashtags)).toBe(true)
      expect(body.hashtags).toContain('NhipDieuXanh')
      expect(body.hashtags).toContain('BatDongSan')
    })

    it('should use environment variables for model server URL, model name, and token when configured', async () => {
      const originalUrl = process.env.MODEL_SERVER_URL
      const originalName = process.env.MODEL_NAME
      const originalToken = process.env.MODEL_SERVER_TOKEN
      const originalFetch = globalThis.fetch

      process.env.MODEL_SERVER_URL = 'http://custom-server:5000/v1'
      process.env.MODEL_NAME = 'custom-model-for-posts'
      process.env.MODEL_SERVER_TOKEN = 'custom-token-for-posts'

      let fetchedUrl = ''
      let fetchedOptions: any = null

      globalThis.fetch = (async (url: any, options: any) => {
        fetchedUrl = String(url)
        fetchedOptions = options
        return new Response(JSON.stringify({
          choices: [{ message: { content: 'Generated text with #CustomHashtag' } }]
        }), { status: 200 })
      }) as any

      try {
        const payload = {
          propertyType: 'Căn hộ',
          area: 'Cái Răng, Cần Thơ',
          price: '2.5 tỷ',
          tone: 'chuyên nghiệp',
          length: 'ngắn'
        }

        const req = new Request('http://localhost/api/posts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        })

        const res = await postPosts(req)
        expect(res.status).toBe(200)

        const body = await res.json()
        expect(body.text).toBe('Generated text with #CustomHashtag')
        expect(body.hashtags).toContain('CustomHashtag')
        expect(fetchedUrl).toBe('http://custom-server:5000/v1/chat/completions')
        
        const requestBody = JSON.parse(fetchedOptions.body)
        expect(requestBody.model).toBe('custom-model-for-posts')
        expect(fetchedOptions.headers['Authorization']).toBe('Bearer custom-token-for-posts')
      } finally {
        if (originalUrl !== undefined) process.env.MODEL_SERVER_URL = originalUrl
        else delete process.env.MODEL_SERVER_URL
        
        if (originalName !== undefined) process.env.MODEL_NAME = originalName
        else delete process.env.MODEL_NAME

        if (originalToken !== undefined) process.env.MODEL_SERVER_TOKEN = originalToken
        else delete process.env.MODEL_SERVER_TOKEN

        globalThis.fetch = originalFetch
      }
    })
  })

  describe('RAG Legal Assistant (POST /api/faq/query)', () => {
    it('should query and return answers with valid document citations for valid question', async () => {
      const payload = {
        question: 'Quy trình pháp lý và 1/500 dự án Nhịp Điệu Xanh ra sao?'
      }

      const req = new Request('http://localhost/api/faq/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const res = await postFAQQuery(req)
      expect(res.status).toBe(200)

      const body = await res.json()
      expect(typeof body.answer).toBe('string')
      expect(body.answer.length).toBeGreaterThan(0)
      expect(body.fallback_triggered).toBe(false)
      expect(Array.isArray(body.citations)).toBe(true)
      expect(body.citations.length).toBeGreaterThan(0)
      expect(body.citations[0].documentName).toBeDefined()
      expect(body.citations[0].reference).toBeDefined()
    })

    it('should trigger fallback and log email alert when question matches no keywords', async () => {
      const payload = {
        question: 'Dự báo thời tiết Cần Thơ ngày mai thế nào?'
      }

      const req = new Request('http://localhost/api/faq/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      const res = await postFAQQuery(req)
      expect(res.status).toBe(200)

      const body = await res.json()
      expect(body.fallback_triggered).toBe(true)
      expect(body.citations).toEqual([])
      expect(body.answer).toContain('Cảm ơn bạn đã đặt câu hỏi')
    })
  })

  describe('Blockchain Notarization', () => {
    it('should query unlocked accounts and successfully notarize a lead hash on geth dev node', async () => {
      const leadId = crypto.randomUUID()
      const leadHash = crypto.createHash('sha256').update(leadId).digest('hex')

      const txHash = await notarizeLeadOnBlockchain(leadId, leadHash)
      expect(txHash).not.toBeNull()
      expect(txHash).toMatch(/^0x([a-fA-F0-9]{64}|0)$/)
    })
  })
})
