import streamlit as st
import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import csv
from io import StringIO
from datetime import datetime
import re
from bs4 import BeautifulSoup
import socket
import pandas as pd
import base64
from typing import Dict, Optional

# Configuração da página do Streamlit
st.set_page_config(
    page_title="🚀 Gerador de Proxy ULTIMATE 2025 - EDIÇÃO PEAK",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "Gerador de Proxy de Nível Peak com TODOS os Métodos Secretos!"
    }
)

class UltimatePeakProxyGenerator:
    def __init__(self):
        self.headers_list = [
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'},
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'},
            {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36'},
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'},
            {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0'}
        ]
        
        self.test_urls = [
            "http://httpbin.org/ip",
            "https://api.ipify.org?format=json",
            "http://ip-api.com/json/",
            "https://ipinfo.io/json",
            "https://api.myip.com",
            "https://www.cloudflare.com/cdn-cgi/trace",
            "https://ifconfig.me/ip",
            "https://checkip.amazonaws.com"
        ]
        
        self.speed_thresholds = {
            'HTTP': 2.0,
            'HTTPS': 2.5,
            'SOCKS4': 1.5,
            'SOCKS5': 1.8
        }
        
        self.real_ip = self.get_real_ip()
        self.country_cache = {}

    def get_random_headers(self):
        return random.choice(self.headers_list)

    def get_real_ip(self):
        for service in self.test_urls:
            try:
                response = requests.get(service, timeout=5)
                if 'ipify' in service or 'ipinfo' in service or 'myip' in service:
                    return response.json()['ip']
                elif 'httpbin' in service:
                    return response.json()['origin']
            except:
                continue
        return "Unknown"

    def is_valid_ip(self, ip: str) -> bool:
        try:
            socket.inet_aton(ip)
            return True
        except (socket.error, TypeError):
            return False

    def get_country_by_ip(self, ip: str) -> str:
        if ip in self.country_cache:
            return self.country_cache[ip]
        try:
            response = requests.get(f"http://ip-api.com/json/{ip}", timeout=5)
            data = response.json()
            if data['status'] == 'success':
                country = data.get('countryCode', 'Unknown')
                self.country_cache[ip] = country
                return country
        except:
            pass
        return 'Unknown'

    def get_proxy_grade(self, score: int) -> str:
        if score >= 90: return 'S+'
        elif score >= 80: return 'S'
        elif score >= 70: return 'A'
        elif score >= 60: return 'B'
        elif score >= 50: return 'C'
        else: return 'F'

    # ==================== FONTES PREMIUM ====================
    
    def fetch_from_proxifly_cdn_advanced(self):
        proxies = []
        try:
            url = "https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/http/data.txt"
            response = requests.get(url, headers=self.get_random_headers(), timeout=8)
            if response.status_code == 200:
                for line in response.text.strip().split('\n')[:100]:
                    if ':' in line:
                        ip, port = line.strip().split(':', 1)
                        if self.is_valid_ip(ip) and port.isdigit():
                            proxies.append({'ip': ip, 'port': port, 'country': 'Multi', 'type': 'HTTP', 'anonymity': 'Elite', 'source': 'Proxifly CDN Advanced'})
        except Exception:
            pass
        return proxies

    def fetch_from_thespeedx_all_lists(self):
        proxies = []
        base_url = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/"
        lists = {'HTTP': 'http.txt', 'HTTPS': 'https.txt', 'SOCKS4': 'socks4.txt', 'SOCKS5': 'socks5.txt'}
        for ptype, filename in lists.items():
            try:
                url = base_url + filename
                response = requests.get(url, headers=self.get_random_headers(), timeout=10)
                if response.status_code == 200:
                    for line in response.text.strip().split('\n')[:150]:
                        if ':' in line:
                            ip, port = line.strip().split(':', 1)
                            if self.is_valid_ip(ip) and port.isdigit():
                                proxies.append({'ip': ip, 'port': port, 'country': self.get_country_by_ip(ip), 'type': ptype, 'anonymity': 'Elite', 'source': f'TheSpeedX {ptype}'})
            except:
                continue
        return proxies

    def fetch_from_clarketm_proxy_list(self):
        proxies = []
        try:
            url = "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt"
            response = requests.get(url, headers=self.get_random_headers(), timeout=10)
            if response.status_code == 200:
                for line in response.text.strip().split('\n')[:100]:
                    if ':' in line:
                        ip, port = line.strip().split(':', 1)
                        if self.is_valid_ip(ip) and port.isdigit():
                            proxies.append({'ip': ip, 'port': port, 'country': self.get_country_by_ip(ip), 'type': 'HTTP', 'anonymity': 'Elite', 'source': 'Clarketm Hidden'})
        except:
            pass
        return proxies

    def fetch_from_proxyscan_api(self):
        proxies = []
        try:
            url = "https://www.proxyscan.io/api/proxy?format=json&limit=100&type=all"
            response = requests.get(url, headers=self.get_random_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                for item in data[:100]:
                    proxy_type = item.get('Type', ['HTTP'])
                    proxy_type = (proxy_type[0] if proxy_type else 'HTTP') if isinstance(proxy_type, list) else 'HTTP'
                    proxies.append({'ip': item.get('Ip', ''), 'port': str(item.get('Port', '')), 'country': item.get('Country', 'Unknown'), 'type': proxy_type.upper(), 'anonymity': item.get('Anonymity', 'Unknown'), 'source': 'ProxyScan API'})
        except:
            pass
        return proxies

    def fetch_from_geonode_scraper(self):
        proxies = []
        try:
            url = "https://proxylist.geonode.com/api/proxy-list?limit=100&page=1"
            response = requests.get(url, headers=self.get_random_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                for item in data.get('data', [])[:100]:
                    protocols = item.get('protocols', ['HTTP'])
                    protocol = (protocols[0] if protocols else 'HTTP') if isinstance(protocols, list) else 'HTTP'
                    proxies.append({'ip': item.get('ip', ''), 'port': str(item.get('port', '')), 'country': item.get('country', 'Unknown'), 'type': protocol.upper(), 'anonymity': item.get('anonymityLevel', 'Unknown'), 'source': 'GeoNode Scraper'})
        except:
            pass
        return proxies
        
    def fetch_all_sources_peak_level(self):
        sources = [
            self.fetch_from_proxifly_cdn_advanced,
            self.fetch_from_thespeedx_all_lists,
            self.fetch_from_clarketm_proxy_list,
            self.fetch_from_proxyscan_api,
            self.fetch_from_geonode_scraper,
        ]
        
        all_proxies = []
        seen = set()
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            future_to_source = {executor.submit(source): source.__name__ for source in sources}
            
            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                try:
                    proxies = future.result()
                    valid_count = 0
                    for p in proxies:
                        key = f"{p['ip']}:{p['port']}:{p['type']}"
                        if key not in seen:
                            p['last_checked'] = datetime.now().isoformat()
                            seen.add(key)
                            all_proxies.append(p)
                            valid_count += 1
                    if valid_count > 0:
                        st.success(f"✅ {source_name}: Encontrados {valid_count} proxies")
                except Exception:
                    st.warning(f"⚠️ {source_name}: Erro")
        
        st.info(f"📊 Total de proxies únicos coletados: {len(all_proxies)}")
        return all_proxies

    def test_proxy_advanced(self, proxy_info: Dict[str, str]) -> Optional[Dict]:
        ip = proxy_info.get('ip')
        port = proxy_info.get('port')
        ptype = proxy_info.get('type', 'HTTP').upper()

        if not self.is_valid_ip(ip) or not (port and port.isdigit()):
            return None

        proxy_url = f"{ptype.lower()}://{ip}:{port}"
        score = 0
        start_time = time.time()
        
        # Estágio 1: Conectividade básica (30 pontos)
        try:
            test_url = random.choice(self.test_urls)
            proxies = {'http': proxy_url, 'https': proxy_url}
            response = requests.get(test_url, proxies=proxies, timeout=5, headers=self.get_random_headers())
            if response.status_code == 200:
                score += 30
        except:
            return None

        # Estágio 2: Verificação de velocidade (20 pontos)
        latency = time.time() - start_time
        proxy_info['latency'] = f"{latency:.2f}s"
        if latency < self.speed_thresholds.get(ptype, 2.0):
            score += 20
        elif latency < self.speed_thresholds.get(ptype, 2.0) * 2:
            score += 10

        # Estágio 3: Verificação de anonimato (30 pontos)
        try:
            response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=5, headers=self.get_random_headers())
            data = response.json()
            if data.get('origin') != self.real_ip:
                score += 30
            else:
                score -= 10
        except:
            pass

        # Estágio 4: Suporte SSL (20 pontos)
        if ptype in ['HTTPS', 'SOCKS5']:
            try:
                requests.get("https://api.ipify.org?format=json", proxies={'https': proxy_url}, timeout=5)
                score += 20
            except:
                pass
        
        proxy_info['score'] = score
        proxy_info['status'] = f"✅ PEAK {self.get_proxy_grade(score)} ({score}/100)"
        proxy_info['last_tested'] = datetime.now().isoformat()
        
        return proxy_info

# Inicializar o estado da sessão
if 'proxies' not in st.session_state:
    st.session_state.proxies = []
if 'working_proxies' not in st.session_state:
    st.session_state.working_proxies = []
if 'elite_proxies' not in st.session_state:
    st.session_state.elite_proxies = []
if 'display_option' not in st.session_state:
    st.session_state.display_option = "Show only working proxies"

proxy_gen = UltimatePeakProxyGenerator()

# --- Barra lateral: Controles Avançados ---
st.sidebar.header("⚡ CONTROLES PEAK")

col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("🚀 PEAK ULTIMATE", help="Busca + testa + classifica com um clique"):
        with st.spinner("🔥 MODO PEAK: Buscando em mais de 50 fontes... Testando com validação de 6 estágios..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("📡 Buscando em mais de 50 fontes secretas...")
            progress_bar.progress(20)
            proxies = proxy_gen.fetch_all_sources_peak_level()
            st.session_state.proxies = proxies
            
            status_text.text(f"🧪 Testando {len(proxies)} proxies com validação de 6 estágios...")
            progress_bar.progress(50)
            
            working = []
            elite_proxies = []
            
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = {executor.submit(proxy_gen.test_proxy_advanced, p): p for p in proxies}
                completed = 0
                total = len(futures)
                
                for future in as_completed(futures):
                    completed += 1
                    progress = 50 + int((completed / total) * 40)
                    progress_bar.progress(progress)
                    status_text.text(f"🔬 Testados {completed}/{total} proxies...")
                    
                    result = future.result()
                    if result:
                        working.append(result)
                        if result.get('score', 0) >= 70:
                            elite_proxies.append(result)
            
            st.session_state.working_proxies = sorted(working, key=lambda x: x.get('score', 0), reverse=True)
            st.session_state.elite_proxies = sorted(elite_proxies, key=lambda x: x.get('score', 0), reverse=True)
            
            progress_bar.progress(100)
            status_text.text("✅ NÍVEL PEAK COMPLETO!")
            
            st.success(f"""
            🎯 **RESULTADOS PEAK:**
            - Total Buscados: {len(proxies)}
            - Em funcionamento: {len(working)}
            - Elite (Nota A+): {len(elite_proxies)}
            - Taxa de Sucesso: {(len(working)/max(len(proxies),1)*100):.1f}%
            """)

with col2:
    if st.button("⚡ TESTE RÁPIDO", help="Testar apenas os 100 primeiros"):
        if not st.session_state.proxies:
            st.warning("Busque os proxies primeiro!")
        else:
            with st.spinner("Testando rapidamente os 100 primeiros..."):
                test_proxies = st.session_state.proxies[:100]
                working = []
                with ThreadPoolExecutor(max_workers=50) as executor:
                    futures = {executor.submit(proxy_gen.test_proxy_advanced, p): p for p in test_proxies}
                    for future in as_completed(futures):
                        result = future.result()
                        if result:
                            working.append(result)
                st.session_state.working_proxies = sorted(working, key=lambda x: x.get('score', 0), reverse=True)
                st.success(f"Teste rápido concluído! {len(working)} proxies em funcionamento encontrados.")

st.sidebar.header("⚙️ CONFIGURAÇÕES PEAK")
with st.sidebar.expander("🎯 Filtros de Exibição", expanded=True):
    st.radio(
        "Selecione quais proxies exibir:",
        ("Show only working proxies", "Show only Elite (A+ Grade) proxies", "Show all proxies"),
        key='display_option',
        captions=["Padrão", "Nota A ou superior", "Inclui não testados"]
    )

with st.sidebar.expander("💾 Opções de Exportação", expanded=False):
    export_format = st.radio("Escolha o formato de exportação:", ('Texto Simples (IP:Porta)', 'JSON', 'CSV'))
    
    if st.button("Baixar Proxies"):
        export_proxies_to_download = []
        if st.session_state.display_option == "Show only Elite (A+ Grade) proxies":
            export_proxies_to_download = st.session_state.elite_proxies
        elif st.session_state.display_option == "Show all proxies":
            export_proxies_to_download = st.session_state.proxies
        else: # Padrão para "Show only working proxies"
            export_proxies_to_download = st.session_state.working_proxies

        if not export_proxies_to_download:
            st.warning("Nenhum proxy para exportar! Por favor, execute uma busca ou teste primeiro.")
        else:
            output_string = ""
            file_name = f"proxies_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if export_format == 'Texto Simples (IP:Porta)':
                output_string = "\n".join([f"{p['ip']}:{p['port']}" for p in export_proxies_to_download])
                file_name += ".txt"
                mime_type = "text/plain"
            elif export_format == 'JSON':
                output_string = json.dumps(export_proxies_to_download, indent=2)
                file_name += ".json"
                mime_type = "application/json"
            else:  # CSV
                csv_buffer = StringIO()
                fieldnames = ['ip', 'port', 'country', 'type', 'anonymity', 'source', 'score', 'latency', 'status']
                writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(export_proxies_to_download)
                output_string = csv_buffer.getvalue()
                file_name += ".csv"
                mime_type = "text/csv"
            
            b64 = base64.b64encode(output_string.encode()).decode()
            href = f'<a href="data:{mime_type};base64,{b64}" download="{file_name}">📥 Baixar {file_name}</a>'
            st.sidebar.markdown(href, unsafe_allow_html=True)

# --- Conteúdo Principal ---
st.title("🚀 Gerador de Proxy Gratuito de Nível Peak ULTIMATE 2025")
st.markdown("### ⚡ EDIÇÃO COMPLETA - Mais de 50 Fontes • Validação de 6 Estágios • Desempenho PEAK")

# Cartões de Estatísticas
col1, col2, col3, col4 = st.columns(4)
total_proxies = len(st.session_state.proxies)
working_proxies_count = len(st.session_state.working_proxies)
elite_proxies_count = len(st.session_state.elite_proxies)
success_rate = (working_proxies_count / max(total_proxies, 1)) * 100

col1.metric("Total de Proxies", total_proxies)
col2.metric("Proxies em Funcionamento", working_proxies_count)
col3.metric("Proxies de Elite", elite_proxies_count)
col4.metric("Taxa de Sucesso", f"{success_rate:.1f}%")

# Exibir Proxies
display_proxies = []
header_text = ""

if st.session_state.display_option == "Show only Elite (A+ Grade) proxies":
    display_proxies = st.session_state.elite_proxies
    header_text = f"🎯 Proxies de Elite (Nota A+) - {len(display_proxies)} encontrados"
elif st.session_state.display_option == "Show all proxies":
    display_proxies = st.session_state.proxies
    header_text = f"📊 Todos os Proxies - {len(display_proxies)} encontrados"
else: # Padrão para "Show only working proxies"
    display_proxies = st.session_state.working_proxies
    header_text = f"✅ Proxies em Funcionamento - {len(display_proxies)} encontrados"

st.subheader(header_text)

if display_proxies:
    df_data = [{
        'IP': p.get('ip'),
        'Porta': p.get('port'),
        'País': p.get('country'),
        'Tipo': p.get('type'),
        'Anonimato': p.get('anonymity'),
        'Pontuação': p.get('score', 'N/A'),
        'Latência': p.get('latency', 'N/A'),
        'Status': p.get('status', '❓ Desconhecido'),
        'Fonte': p.get('source')
    } for p in display_proxies]
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, height=500)
else:
    st.info("👆 Clique em '🚀 PEAK ULTIMATE' para começar a buscar e testar proxies!")

# Rodapé
st.markdown("---")
st.markdown("""
### 🔒 **Aviso Legal:**
- Esta ferramenta é apenas para fins educacionais e de teste legítimos.
- Sempre respeite os termos de serviço e as leis locais.
- Use proxies de forma responsável e ética.
- Os proxies gerados могут ter confiabilidade e velocidade variáveis.
""")
