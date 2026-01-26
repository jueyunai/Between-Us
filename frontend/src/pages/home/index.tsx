import React, { useEffect, useState } from 'react'
import { View, Text } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { Button, Dialog } from '@nutui/nutui-react-taro'
import { getUserProfile, generateBindingCode, bindPartner, logout } from '../../services/api'
import { getUserInfo, setUserInfo, clearAuth, UserInfo } from '../../utils/storage'
import './index.scss'

const HomePage: React.FC = () => {
  const [user, setUser] = useState<UserInfo | null>(null)
  const [bindCode, setBindCode] = useState('')
  const [showBindDialog, setShowBindDialog] = useState(false)
  const [inputCode, setInputCode] = useState('')

  useEffect(() => {
    loadUserProfile()
  }, [])

  const loadUserProfile = async () => {
    // 先从本地获取
    const localUser = getUserInfo()
    if (localUser) {
      setUser(localUser)
    }

    // 从服务器刷新
    const res = await getUserProfile()
    if (res.success && res.user) {
      setUser(res.user)
      setUserInfo(res.user)
    } else if (!localUser) {
      // 未登录，跳转登录页
      Taro.redirectTo({ url: '/pages/login/index' })
    }
  }

  const handleGenerateCode = async () => {
    const res = await generateBindingCode()
    if (res.success && res.data?.binding_code) {
      setBindCode(res.data.binding_code)
      Taro.showModal({
        title: '绑定码',
        content: `您的绑定码是：${res.data.binding_code}\n请将此码分享给您的伴侣`,
        showCancel: false,
      })
    } else {
      Taro.showToast({ title: res.message || '生成失败', icon: 'none' })
    }
  }

  const handleBindPartner = async () => {
    if (!inputCode.trim()) {
      Taro.showToast({ title: '请输入绑定码', icon: 'none' })
      return
    }

    const res = await bindPartner(inputCode.trim())
    if (res.success) {
      Taro.showToast({ title: '绑定成功', icon: 'success' })
      setShowBindDialog(false)
      setInputCode('')
      loadUserProfile()
    } else {
      Taro.showToast({ title: res.message || '绑定失败', icon: 'none' })
    }
  }

  const handleLogout = async () => {
    await logout()
    clearAuth()
    Taro.redirectTo({ url: '/pages/login/index' })
  }

  const navigateTo = (url: string) => {
    Taro.navigateTo({ url })
  }

  return (
    <View className='home-page'>
      <View className='home-header'>
        <Text className='greeting'>你好，{user?.nickname || '用户'} 💝</Text>
        <Text className='subtitle'>今天想聊点什么？</Text>
      </View>

      <View className='menu-section'>
        <View className='menu-card coach' onClick={() => navigateTo('/pages/coach/index')}>
          <View className='card-icon'>🧘</View>
          <View className='card-content'>
            <Text className='card-title'>AI 情感教练</Text>
            <Text className='card-desc'>专属的情感倾诉与建议</Text>
          </View>
        </View>

        <View className='menu-card lounge' onClick={() => navigateTo('/pages/lounge/index')}>
          <View className='card-icon'>💬</View>
          <View className='card-content'>
            <Text className='card-title'>情感客厅</Text>
            <Text className='card-desc'>与伴侣一起畅聊</Text>
          </View>
        </View>
      </View>

      <View className='partner-section'>
        <Text className='section-title'>伴侣绑定</Text>
        {user?.has_partner ? (
          <View className='partner-status bound'>
            <Text className='status-icon'>💑</Text>
            <Text className='status-text'>已绑定伴侣</Text>
          </View>
        ) : (
          <View className='partner-actions'>
            <Button className='action-btn' onClick={handleGenerateCode}>
              生成绑定码
            </Button>
            <Button className='action-btn outline' onClick={() => setShowBindDialog(true)}>
              输入绑定码
            </Button>
          </View>
        )}
      </View>

      <View className='footer-actions'>
        <Button className='logout-btn' fill='none' onClick={handleLogout}>
          退出登录
        </Button>
      </View>

      <Dialog
        visible={showBindDialog}
        title='绑定伴侣'
        onConfirm={handleBindPartner}
        onCancel={() => setShowBindDialog(false)}
      >
        <View className='bind-dialog-content'>
          <input
            className='bind-input'
            placeholder='请输入伴侣的绑定码'
            value={inputCode}
            onChange={(e) => setInputCode(e.target.value)}
          />
        </View>
      </Dialog>
    </View>
  )
}

export default HomePage
