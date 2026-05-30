import { NextResponse } from 'next/server'
import crypto from 'crypto'
import { removeAccents } from '@/lib/utils'



/**
 * Formats a string to be suitable as a hashtag.
 * @param str The string to clean.
 * @returns A formatted hashtag string.
 */
function cleanHashtag(str: string): string {
  return removeAccents(str)
    .replace(/[^a-zA-Z0-9]/g, '')
}

export async function POST(req: Request) {
  try {
    const body = await req.json()
    const { propertyType, area, price, tone, length } = body

    // 1. Validate inputs
    if (!propertyType || !area || !price || !tone || !length) {
      return NextResponse.json(
        { error: 'missing_fields', message: 'Vui lòng cung cấp đầy đủ thông tin: propertyType, area, price, tone, length.' },
        { status: 400 }
      )
    }

    const postId = crypto.randomUUID()
    let text = ''
    let hashtags: string[] = []

    // 2. Call local LLM with timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 15000) // Increased to 15s to accommodate 35B local model

    try {
      const serverUrl = process.env.MODEL_SERVER_URL || 'http://localhost:11437'
      const modelName = process.env.MODEL_NAME || 'mlx-community/Qwen3.6-35B-A3B-4bit'
      const token = process.env.MODEL_SERVER_TOKEN || 'mlx'

      const completionsUrl = serverUrl.includes('/v1/') || serverUrl.endsWith('/v1')
        ? (serverUrl.endsWith('/v1') ? `${serverUrl}/chat/completions` : serverUrl)
        : `${serverUrl.replace(/\/$/, '')}/v1/chat/completions`

      const response = await fetch(completionsUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: modelName,
          messages: [
            {
              role: 'system',
              content: 'Bạn là chuyên viên viết bài đăng quảng cáo bất động sản của dự án Nhịp Điệu Xanh. Hãy viết một bài đăng mạng xã hội (Facebook/Zalo) quảng cáo bán bất động sản hấp dẫn, chuyên nghiệp và đầy sinh khí. Cần nêu rõ thông tin loại nhà đất, khu vực và giá cả.'
            },
            {
              role: 'user',
              content: `Tạo bài viết quảng cáo bất động sản với thông tin sau:
- Loại hình bất động sản: ${propertyType}
- Khu vực: ${area}
- Giá bán: ${price}
- Giọng văn (tone): ${tone}
- Độ dài bài viết: ${length}`
            }
          ],
          temperature: 0.7
        }),
        signal: controller.signal
      })

      if (response.ok) {
        const data = await response.json()
        const content = data.choices?.[0]?.message?.content || ''
        if (content.trim()) {
          text = content
          // Extract hashtags from the generated text if any with Unicode letters/numbers support
          const hashtagsMatches = content.match(/#[_\p{L}\p{N}]+/gu)
          if (hashtagsMatches) {
            hashtags = hashtagsMatches.map((tag: string) => tag.replace('#', ''))
          }
        }
      }
    } catch (llmError) {
      console.warn('[POST /api/posts] Local LLM call failed or offline. Using fallback template.', llmError)
    } finally {
      clearTimeout(timeoutId)
    }

    // 3. Fallback post generator if LLM failed/offline or returned empty
    if (!text) {
      text = `🏡 CƠ HỘI SỞ HỮU BẤT ĐỘNG SẢN TIỀN NĂNG TẠI ${area.toUpperCase()}!

Cần bán gấp ${propertyType} vị trí đắc địa tại khu vực ${area}.
✨ Thông tin chi tiết:
- Loại hình: ${propertyType}
- Vị trí: ${area}
- Giá bán: ${price}
- Giọng văn: ${tone}
- Độ dài bài viết: ${length}

Đây là cơ hội đầu tư và an cư lý tưởng với tiềm năng sinh lời cao, giao thông thuận tiện và hạ tầng đồng bộ. 

📞 Liên hệ ngay Nhịp Điệu Xanh để nhận thông tin chi tiết và lịch xem thực tế!`
    }

    // Ensure we have relevant hashtags
    const defaultTags = [
      'NhipDieuXanh',
      'BatDongSan',
      cleanHashtag(propertyType),
      cleanHashtag(area)
    ].filter(Boolean)

    hashtags = Array.from(new Set([...hashtags, ...defaultTags]))

    return NextResponse.json({
      id: postId,
      text,
      hashtags
    })

  } catch (error: unknown) {
    const errMsg = error instanceof Error ? error.message : String(error)
    console.error('[POST /api/posts] Error:', errMsg)
    return NextResponse.json(
      { error: 'server_error', message: 'Đã xảy ra lỗi trên hệ thống. Xin vui lòng thử lại sau.' },
      { status: 500 }
    )
  }
}
