const { createApp, ref, computed, onBeforeUnmount, onMounted } = Vue;
const { createVuetify, useDisplay, useTheme } = Vuetify;

const vuetify = createVuetify();

const app = createApp({
    setup() {
        const { smAndDown } = useDisplay()
        const theme = useTheme()

        const isConnected = ref(false)
        const serverAddress = ref(localStorage.getItem('serverAddress') || '')
        const ws = ref(null)
        const status = ref('idle')
        const scanTime = ref(0)
        const devices = ref({})
        const storedDevices = ref([])
        const currentSimulatingDevice = ref('')
        const manufacturer = ref({})
        const searchQuery = ref('')
        const sortBy = ref([{ key: 'rssi', order: 'desc' }])

        const scannedDevicesHeaders = [
            { title: '地址', key: 'addr' },
            { title: '信号强度', key: 'rssi' },
            { title: '数据', key: 'data', cellProps: { class: 'data monospace' } },
            { title: '制造商', key: 'manufacturer' },
            { title: '操作', key: 'action', sortable: false }
        ]

        const storedDevicesHeaders = [
            { title: '名称', key: 'alias' },
            { title: '地址', key: 'addr' },
            { title: '信号强度', key: 'rssi' },
            { title: '数据', key: 'data', cellProps: { class: 'data monospace' } },
            { title: '制造商', key: 'manufacturer' },
            { title: '操作', key: 'action', sortable: false }
        ]

        const scannedDevices = computed(() => {
            return Object.values(devices.value)
        })

        const colorType = computed(() => {
            switch (status.value) {
                case 'scanning': return 'blue'
                case 'advertising': return 'green'
                default: return 'grey'
            }
        })

        const statusIconType = computed(() => {
            switch (status.value) {
                case 'scanning': return 'mdi-magnify'
                case 'advertising': return 'mdi-bluetooth-audio'
                default: return '$success'
            }
        })

        function loadStoredDevices() {
            if (ws.value && ws.value.readyState === WebSocket.OPEN) {
                ws.value.send('store\r\n')
            }
        }

        function saveStoredDevices() {
            if (ws.value && ws.value.readyState === WebSocket.OPEN) {
                const base64Data = btoa(JSON.stringify(storedDevices.value))
                ws.value.send(`store ${base64Data}\r\n`)
            }
        }

        function connectServer() {
            if (ws.value) {
                ws.value.close()
            }

            try {
                ws.value = new WebSocket(`ws://${serverAddress.value}`)

                ws.value.onopen = () => {
                    isConnected.value = true
                    localStorage.setItem('serverAddress', serverAddress.value)
                    loadStoredDevices()
                    ws.value.send('status\r\n')
                    devices.value = JSON.parse(localStorage.getItem('devices') || '{}')
                    loadManufacturers()
                }

                ws.value.onmessage = (event) => {
                    const message = event.data
                    console.log('Message:', message)
                    if (message.startsWith('new-device')) {
                        const [, addr, rssi, ...dataParts] = message.split(' ')
                        devices.value[addr] = {
                            addr,
                            rssi: parseInt(rssi),
                            data: dataParts.join(' ')
                        }
                        localStorage.setItem('devices', JSON.stringify(devices.value))
                    } else if (message.startsWith('status')) {
                        const [, newStatus] = message.split(' ')
                        status.value = newStatus
                        if (newStatus !== 'advertising') {
                            currentSimulatingDevice.value = ''
                        }
                    } else if (message.startsWith('stored-devices')) {
                        try {
                            const base64Data = message.split(' ')[1]
                            const decodedData = atob(base64Data)
                            storedDevices.value = JSON.parse(decodedData)
                        } catch (error) {
                            console.error('Error parsing stored devices:', error)
                        }
                    }
                }

                ws.value.onclose = () => {
                    isConnected.value = false
                }
            } catch (error) {
                alert('连接失败: ' + error.message)
            }
        }

        function startScan() {
            ws.value.send(`scan ${scanTime.value}\r\n`)
            if (scanTime.value > 0) {
                setTimeout(() => {
                    status.value = 'idle'
                }, scanTime.value * 1000)
            }
        }

        function stopOperation() {
            ws.value.send('stop\r\n')
        }

        function storeDevice(device) {
            const alias = prompt('请输入设备别名：')
            if (alias) {
                storedDevices.value.push({
                    ...device,
                    alias
                })
                saveStoredDevices()
            }
        }

        function simulateDevice(device) {
            ws.value.send(`simulate ${device.data}\r\n`)
            currentSimulatingDevice.value = device.alias
        }

        function editAlias(index) {
            const newAlias = prompt('请输入新的别名：', storedDevices.value[index].alias)
            if (newAlias) {
                storedDevices.value[index].alias = newAlias
                saveStoredDevices()
            }
        }

        function deleteDevice(index) {
            if (confirm('确定要删除这个设备吗？')) {
                storedDevices.value.splice(index, 1)
                saveStoredDevices()
            }
        }

        function loadManufacturers() {
            fetch('/manufacturer.json')
                .then(response => response.json())
                .then(data => {
                    manufacturer.value = data
                })
                .catch(error => {
                    console.error('Error loading manufacturer data:', error)
                })
        }

        function getManufacturer(data) {
            let bytes = []
            let na = 'N/A'
            for (let c = 0; c < data.length; c += 2)
                bytes.push(parseInt(data.substr(c, 2), 16))
            while (bytes.length > 0) {
                const length = bytes.shift()
                const type = bytes.shift()
                if (type === 0xff) {
                    const idx = bytes[1] * 256 + bytes[0]
                    return manufacturer.value[idx] || na
                }
                bytes = bytes.slice(length - 1)
            }
            return na
        }

        function clearDevices() {
            devices.value = {}
            localStorage.removeItem('devices')
        }

        onMounted(() => {
            if (serverAddress.value) {
                connectServer()
            }

            const beforeUnloadHandler = (event) => {
                if (status.value !== 'idle') {
                    event.preventDefault()
                    event.returnValue = '当前有正在进行的操作，确定要离开吗？'
                    return event.returnValue
                }
            }
            window.addEventListener('beforeunload', beforeUnloadHandler)

            onBeforeUnmount(() => {
                window.removeEventListener('beforeunload', beforeUnloadHandler)
            })

            theme.global.name.value = localStorage.getItem('theme') || 'light'
        })

        function toggleTheme () {
            theme.global.name.value = theme.global.current.value.dark ? 'light' : 'dark'
            localStorage.setItem('theme', theme.global.name.value)
        }

        return {
            smAndDown,
            isConnected,
            serverAddress,
            status,
            scanTime,
            devices,
            storedDevices,
            currentSimulatingDevice,
            searchQuery,
            scannedDevicesHeaders,
            storedDevicesHeaders,
            scannedDevices,
            colorType,
            statusIconType,
            connectServer,
            startScan,
            stopOperation,
            storeDevice,
            simulateDevice,
            editAlias,
            deleteDevice,
            clearDevices,
            sortBy,
            getManufacturer,
            toggleTheme
        }
    }
});
app.use(vuetify).mount('#app')

console.log(vuetify.display.mobile.value)