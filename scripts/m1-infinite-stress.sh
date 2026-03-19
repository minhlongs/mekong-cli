#!/bin/bash
# M1 Infinite Stress Loop (CPU, RAM, SSD)
# Requested by User: "kích hoạt vòng lặp vô tận k dừng M1 Ram ssd liên tục k dừng"

echo "🔥 Kích hoạt Vòng Lặp Vô Tận M1 (RAM + SSD + CPU) 🔥"

stress_cpu_ram() {
    local seed=$1
    while true; do
        # Do heavy math + array allocation to stress CPU/RAM
        declare -a dummy_array
        for i in {1..20000}; do
            dummy_array[$i]=$(echo "scale=10; $i * $i / 3.14159 * $seed" | bc)
        done
        unset dummy_array
    done
}

stress_ssd() {
    local id=$1
    local test_file="/tmp/stress_ssd_inf_${id}.dat"
    while true; do
        # Write 50MB, read, delete
        dd if=/dev/urandom of="$test_file" bs=1m count=50 2>/dev/null
        cat "$test_file" > /dev/null
        rm -f "$test_file"
    done
}

# Cấm sleep
caffeinate -dims &

# Chạy 3 workers đập CPU/RAM, 2 workers đập SSD (tổng 5 luồng tải nặng)
for i in {1..3}; do
    stress_cpu_ram $i &
done

for i in {1..2}; do
    stress_ssd $i &
done

echo "🚀 Stress Test đã cắm rễ vào nền. Các luồng đập RAM/SSD đang chạy."

while true; do
    sleep 3600
done
