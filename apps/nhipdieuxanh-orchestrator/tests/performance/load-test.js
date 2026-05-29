import http from 'k6/http';
import { check, sleep } from 'k6';

// Cấu hình k6 load test cho 10,000 người dùng đồng thời (Virtual Users - VUs)
// Ramp-up nhanh lên 10,000 VUs, duy trì tải, và ramp-down
export const options = {
  stages: [
    { duration: '30s', target: 2000 },  // Ramp-up lên 2,000 VUs trong 30 giây
    { duration: '1m', target: 5000 },   // Tiếp tục ramp-up lên 5,000 VUs trong 1 phút
    { duration: '2m', target: 10000 },  // Đạt đỉnh 10,000 VUs trong 2 phút
    { duration: '3m', target: 10000 },  // Duy trì tải 10,000 VUs trong 3 phút
    { duration: '1m', target: 0 },      // Ramp-down về 0 trong 1 phút
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],   // 95% request phải có latency dưới 500ms
    http_req_failed: ['rate<0.01'],     // Tỷ lệ lỗi tối đa là 1%
  },
};

const BASE_URL = __ENV.GATEWAY_URL || 'http://localhost';

// Tập hợp dữ liệu giả lập cho thị trường Cần Thơ (để test ngẫu nhiên)
const NAMES = ['Nguyễn Văn An', 'Trần Thị Bình', 'Phạm Minh Cường', 'Lê Hoài Nam', 'Vũ Hoàng Yến', 'Đỗ Quốc Khánh', 'Phan Thanh Thảo'];
const PHONES = ['0912345678', '0987654321', '0905123456', '0978999888', '0933445566', '0911223344'];
const EMAILS = ['an.nguyen@gmail.com', 'binh.tran@yahoo.com', 'cuong.pham@outlook.com', 'nam.le@nhipdieuxanh.vn'];
const NEEDS = ['mua ở', 'đầu tư', 'cho con đi học', 'khác'];
const BUDGETS = ['Dưới 2 tỷ', '2 - 5 tỷ', '5 - 10 tỷ', 'Trên 10 tỷ'];
const AREAS = ['Ninh Kiều', 'Cái Răng', 'Bình Thủy', 'Phong Điền', 'Ô Môn'];

function getRandomElement(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

export default function () {
  // Tạo dữ liệu đăng ký Lead ngẫu nhiên
  const payload = JSON.stringify({
    name: getRandomElement(NAMES),
    phone: getRandomElement(PHONES),
    email: getRandomElement(EMAILS),
    need: getRandomElement(NEEDS),
    budget: getRandomElement(BUDGETS),
    area: getRandomElement(AREAS),
    source: 'k6_performance_test'
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-Load-Test': 'true'
    },
  };

  // Gửi POST request đến API Gateway route /api/leads
  const res = http.post(`${BASE_URL}/api/leads`, payload, params);

  // Kiểm tra kết quả trả về
  check(res, {
    'status is 201 or 200': (r) => r.status === 200 || r.status === 201,
    'response has validation id': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body && (body.id !== undefined || body.success === true);
      } catch (e) {
        return false;
      }
    }
  });

  // Nghỉ giữa các request từ 0.5s đến 2s để mô phỏng hành vi người dùng thật
  sleep(Math.random() * 1.5 + 0.5);
}
