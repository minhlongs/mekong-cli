import { test, expect } from '@playwright/test'

test.describe('Luồng đăng ký tư vấn Nhịp Điệu Xanh', () => {
  test.beforeEach(async ({ page }) => {
    // Truy cập trang chủ Landing Page
    await page.goto('http://localhost:3010')
  })

  test('Người dùng đăng ký nhận tư vấn thành công với thông tin đầy đủ', async ({ page }) => {
    // 1. Kiểm tra tiêu đề trang
    await expect(page).toHaveTitle(/Nhịp Điệu Xanh/)

    // 2. Kiểm tra phần Hero hiển thị chính xác
    const heroHeading = page.locator('h1')
    await expect(heroHeading).toContainText('Tìm Nhà Cần Thơ')

    // 3. Điền thông tin vào Form Đăng Ký
    await page.fill('input[name="name"]', 'Nguyễn Văn Kiểm Thử')
    await page.fill('input[name="phone"]', '0912345678')
    await page.fill('input[name="email"]', 'tester@nhipdieuxanh.vn')

    // Chọn các trường Dropdown
    await page.selectOption('select[name="need"]', { value: 'đầu tư' })
    await page.selectOption('select[name="area"]', { value: 'Cái Răng' })
    await page.selectOption('select[name="budget"]', { value: '2 - 3 tỷ' })

    // 4. Submit Form
    const submitButton = page.locator('button[type="submit"]')
    await submitButton.click()

    // 5. Kiểm tra trạng thái thành công (Success state)
    // Sau khi API trả về, UI sẽ hiển thị text chúc mừng
    const successHeading = page.locator('h3')
    await expect(successHeading).toContainText('Đăng Ký Thành Công!')

    const successMessage = page.locator('p')
    await expect(successMessage).toContainText('đội ngũ chuyên viên Nhịp Điệu Xanh sẽ liên hệ')
  })

  test('Hiển thị thông báo lỗi khi không nhập số điện thoại', async ({ page }) => {
    // Chỉ điền tên và bỏ trống số điện thoại
    await page.fill('input[name="name"]', 'Người Mua Thiếu Số')
    
    // Submit Form
    const submitButton = page.locator('button[type="submit"]')
    await submitButton.click()

    // Kiểm tra thông báo lỗi hiển thị
    const errorMessage = page.locator('div:has-text("Vui lòng nhập Số điện thoại")')
    await expect(errorMessage).toBeVisible()
  })

  test('Hiển thị thông báo lỗi khi nhập số điện thoại sai định dạng', async ({ page }) => {
    await page.fill('input[name="name"]', 'Nguyễn Văn A')
    await page.fill('input[name="phone"]', '12345') // Số điện thoại không hợp lệ

    // Submit Form
    const submitButton = page.locator('button[type="submit"]')
    await submitButton.click()

    // Kiểm tra thông báo lỗi định dạng
    const errorMessage = page.locator('div:has-text("Số điện thoại không đúng định dạng")')
    await expect(errorMessage).toBeVisible()
  })
})
