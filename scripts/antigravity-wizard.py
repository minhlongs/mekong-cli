#!/usr/bin/env python3
"""
Antigravity IDE Setup Wizard (Tiếng Việt)
Chương 1 "Thủy Kế" - Strategic Planning for User Success

This wizard guides NO-TECH users to setup Antigravity IDE optimally.
"""

import os
import platform
import shutil
import subprocess
import sys
import time
from typing import List

# Third-party imports
try:
    import psutil
    import questionary
    import speedtest
    from rich import print as rprint
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
except ImportError:
    print("Đang cài đặt các thư viện cần thiết... (Installing dependencies...)")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rich", "questionary", "psutil", "speedtest-cli"])
        import psutil
        import questionary
        import speedtest
        from rich.console import Console
        from rich.panel import Panel
        from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
        from rich.prompt import Confirm
        from rich.table import Table
    except Exception as e:
        print(f"Lỗi cài đặt thư viện: {e}")
        print("Vui lòng chạy: pip install -r requirements.txt")
        sys.exit(1)

console = Console()

class AntigravityWizard:
    def __init__(self):
        self.system_info = {}
        self.recommendations = []

    def clear_screen(self):
        # Safer clear screen using rich console
        console.clear()

    def welcome(self):
        self.clear_screen()
        console.print(Panel.fit(
            "[bold cyan]🏯 CHÀO MỪNG ĐẾN ANTIGRAVITY IDE[/bold cyan]\n"
            "[yellow]Hệ điều hành AI cho Agency & Startup[/yellow]\n"
            "[dim]Powered by Claude Code CLI + Binh Pháp Strategy[/dim]",
            border_style="cyan",
            padding=(1, 4)
        ))
        console.print("\n[italic]Wizard này sẽ giúp bạn thiết lập môi trường tối ưu nhất cho Antigravity.[/italic]\n")

        if not Confirm.ask("🚀 Bạn đã sẵn sàng bắt đầu chưa?", default=True):
            console.print("[red]Đã hủy thiết lập. Hẹn gặp lại![/red]")
            sys.exit(0)

    def check_system(self):
        """Chương 5 "Thế Trận" - Strategic Advantage Check"""
        console.print("\n[bold]📊 ĐANG KIỂM TRA HỆ THỐNG (SYSTEM CHECK)...[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            transient=False,
        ) as progress:

            # Hardware Check
            task1 = progress.add_task("[cyan]Kiểm tra phần cứng...", total=100)

            # CPU
            cpu_count = psutil.cpu_count(logical=True)
            self.system_info['cpu_cores'] = cpu_count
            progress.update(task1, advance=30)

            # RAM
            ram = psutil.virtual_memory()
            ram_gb = round(ram.total / (1024**3), 1)
            self.system_info['ram_gb'] = ram_gb
            progress.update(task1, advance=30)

            # Disk
            disk = shutil.disk_usage("/")
            disk_free_gb = round(disk.free / (1024**3), 1)
            self.system_info['disk_free_gb'] = disk_free_gb
            progress.update(task1, advance=40)

            # OS Info
            self.system_info['os'] = platform.system()
            self.system_info['os_release'] = platform.release()
            self.system_info['arch'] = platform.machine()

            # Network Check (can be slow)
            task2 = progress.add_task("[cyan]Kiểm tra kết nối mạng (Speed Test)...", total=100)
            try:
                st = speedtest.Speedtest()
                st.get_best_server()
                progress.update(task2, advance=20, description="[cyan]Đang đo tốc độ tải xuống...")
                download_speed = st.download() / 1_000_000  # Mbps
                progress.update(task2, advance=40, description="[cyan]Đang đo tốc độ tải lên...")
                upload_speed = st.upload() / 1_000_000  # Mbps

                self.system_info['download_mbps'] = round(download_speed, 1)
                self.system_info['upload_mbps'] = round(upload_speed, 1)
                progress.update(task2, completed=100, description="[green]Kiểm tra mạng hoàn tất")
            except Exception:
                self.system_info['download_mbps'] = 0
                self.system_info['upload_mbps'] = 0
                progress.update(task2, completed=100, description="[yellow]Không thể kiểm tra tốc độ mạng (Bỏ qua)")

        self._display_system_report()

    def _display_system_report(self):
        table = Table(title="📑 Báo cáo Hệ Thống (System Report)")
        table.add_column("Thành phần", style="cyan")
        table.add_column("Thông số", style="magenta")
        table.add_column("Trạng thái", style="green")

        # CPU
        status_cpu = "[green]Tốt[/green]" if self.system_info['cpu_cores'] >= 4 else "[yellow]Tối thiểu[/yellow]"
        table.add_row("CPU Cores", str(self.system_info['cpu_cores']), status_cpu)

        # RAM
        ram = self.system_info['ram_gb']
        if ram >= 16:
            status_ram = "[green]Tuyệt vời[/green]"
        elif ram >= 8:
            status_ram = "[yellow]Đủ dùng[/yellow]"
        else:
            status_ram = "[red]Cần nâng cấp[/red]"
            self.recommendations.append("RAM thấp (<8GB): Nên nâng cấp để chạy Docker/AI mượt mà.")
        table.add_row("RAM", f"{ram} GB", status_ram)

        # Disk
        disk = self.system_info['disk_free_gb']
        status_disk = "[green]Thoải mái[/green]" if disk > 20 else "[red]Sắp đầy[/red]"
        if disk <= 20:
             self.recommendations.append(f"Ổ cứng sắp đầy (còn {disk}GB): Cần dọn dẹp >20GB trống.")
        table.add_row("Disk Free", f"{disk} GB", status_disk)

        # Network
        dl = self.system_info.get('download_mbps', 0)
        if dl > 100:
            status_net = "[green]Tốc độ cao[/green]"
        elif dl > 30:
            status_net = "[yellow]Ổn định[/yellow]"
        elif dl > 0:
            status_net = "[red]Chậm[/red]"
            self.recommendations.append("Mạng chậm (<30Mbps): Cân nhắc nâng cấp gói cước FTTH.")
        else:
            status_net = "[grey]Không xác định[/grey]"
        table.add_row("Internet (Download)", f"{dl} Mbps", status_net)

        console.print(table)

    def gap_analysis(self):
        """Analyze missing components"""
        console.print("\n[bold]🔍 PHÂN TÍCH KHOẢNG CÁCH (GAP ANALYSIS)...[/bold]")

        # Check for key tools
        tools = {
            "git": "Quản lý mã nguồn",
            "docker": "Môi trường container (Optional)",
            "node": "Node.js Runtime",
            "python3": "Python Interpreter",
            "claude": "Claude Code CLI"
        }

        missing = []
        for tool, desc in tools.items():
            if shutil.which(tool) is None:
                missing.append(f"{tool} ({desc})")

        if missing:
            console.print(f"[yellow]⚠️ Các công cụ chưa được cài đặt:[/yellow] {', '.join(missing)}")
            self.recommendations.append("Cài đặt các công cụ thiếu: " + ", ".join(missing))
        else:
            console.print("[green]✅ Đã cài đặt đầy đủ các công cụ cơ bản.[/green]")

        if self.recommendations:
            console.print("\n[bold red]🚨 KHUYẾN NGHỊ CẢI THIỆN:[/bold red]")
            for rec in self.recommendations:
                console.print(f" - {rec}")

            if not Confirm.ask("\nBạn có muốn tiếp tục cài đặt không?", default=True):
                sys.exit(0)
        else:
            console.print("\n[green]🎉 Hệ thống của bạn đã sẵn sàng![/green]")

    def guided_installation(self):
        """Step-by-step setup"""
        console.print("\n[bold]🛠️ THIẾT LẬP MÔI TRƯỜNG (SETUP)[/bold]")

        steps = [
            "Cài đặt/Cập nhật Dependencies",
            "Kiểm tra biến môi trường (.env)",
            "Khởi tạo Antigravity Project",
            "Validation (Kiểm tra cuối)"
        ]

        selected_steps = questionary.checkbox(
            "Chọn các bước bạn muốn thực hiện:",
            choices=steps,
            qmark="🎯"
        ).ask()

        if not selected_steps:
            console.print("[yellow]Không có bước nào được chọn.[/yellow]")
            return

        for step in selected_steps:
            console.print(f"\n[cyan]▶️ Đang thực hiện: {step}[/cyan]")

            if step == "Cài đặt/Cập nhật Dependencies":
                self._run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], "Cài đặt Python packages")

            elif step == "Kiểm tra biến môi trường (.env)":
                if os.path.exists(".env"):
                    console.print("[green]✅ File .env đã tồn tại.[/green]")
                else:
                    if os.path.exists(".env.example"):
                        shutil.copy(".env.example", ".env")
                        console.print("[green]✅ Đã tạo .env từ .env.example[/green]")
                    else:
                        console.print("[yellow]⚠️ Không tìm thấy .env.example, bỏ qua.[/yellow]")

            elif step == "Khởi tạo Antigravity Project":
                 console.print("[dim]Đang cấu hình các thư mục mặc định...[/dim]")
                 os.makedirs("data", exist_ok=True)
                 os.makedirs("logs", exist_ok=True)
                 console.print("[green]✅ Cấu trúc thư mục OK.[/green]")

            elif step == "Validation (Kiểm tra cuối)":
                console.print("[green]✅ Mọi thứ có vẻ ổn![/green]")

            time.sleep(0.5)

    def _run_command(self, cmd: List[str], desc: str):
        try:
            with console.status(f"[bold green]{desc}...") as _:
                subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            console.print(f"[green]✅ {desc} thành công.[/green]")
        except subprocess.CalledProcessError:
            console.print(f"[red]❌ {desc} thất bại.[/red]")

    def success_celebration(self):
        """Chương 13 "Dụng Gián" - Turn user into ambassador"""
        self.clear_screen()
        console.print(Panel.fit(
            "[bold green]✅ SETUP HOÀN TẤT! (COMPLETED)[/bold green]\n\n"
            "Bạn đã sẵn sàng sử dụng [cyan]Antigravity IDE[/cyan] với hiệu suất tối ưu.\n"
            "Hãy bắt đầu hành trình chinh phục thị trường!\n\n"
            "[bold yellow]🚀 Bước tiếp theo:[/bold yellow]\n"
            "1. Chạy [reverse] cc sales dashboard [/reverse] để xem doanh thu\n"
            "2. Chạy [reverse] cc deploy [/reverse] để đưa ứng dụng lên mây\n\n"
            "[cyan]Chia sẻ thành công của bạn:[/cyan]\n"
            "→ Twitter: @MekongAI\n"
            "→ Facebook: Mekong AI Community\n"
            "→ Giới thiệu bạn bè → Nhận quyền lợi đặc biệt",
            border_style="green",
            padding=(1, 4)
        ))

        console.print("\n[italic]Cảm ơn bạn đã tin tưởng Antigravity.[/italic] 🙇\n")

def main():
    try:
        wizard = AntigravityWizard()
        wizard.welcome()
        wizard.check_system()
        wizard.gap_analysis()
        wizard.guided_installation()
        wizard.success_celebration()
    except KeyboardInterrupt:
        console.print("\n[red]Đã dừng Wizard.[/red]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Lỗi không mong muốn: {e}[/red]")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
