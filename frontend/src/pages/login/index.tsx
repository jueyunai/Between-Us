import React, { useState } from 'react'
import { View, Text, Input, Button } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { login, register } from '../../services/api'
import { setToken, setUserInfo } from '../../utils/storage'
import './index.scss'

const LoginPage: React.FC = () => {
  const [isLogin, setIsLogin] = useState(true)
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [nickname, setNickname] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    if (!phone || !password) {
      Taro.showToast({ title: '请填写手机号和密码', icon: 'none' })
      return
    }

    setLoading(true)
    try {
      if (isLogin) {
        const res = await login(phone, password)
        if (res.success && res.token && res.user) {
          setToken(res.token)
          setUserInfo(res.user)
          Taro.showToast({ title: '登录成功', icon: 'success' })
          setTimeout(() => {
            Taro.redirectTo({ url: '/pages/home/index' })
          }, 1000)
        } else {
          Taro.showToast({ title: res.message || '登录失败', icon: 'none' })
        }
      } else {
        const trimmedNickname = nickname.trim()
        const res = await register(phone, password, trimmedNickname || undefined)
        if (res.success) {
          Taro.showToast({ title: '注册成功，请登录', icon: 'success' })
          setIsLogin(true)
          setPassword('')
          setNickname('')
        } else {
          Taro.showToast({ title: res.message || '注册失败', icon: 'none' })
        }
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <View className='login-page'>
      <View className='container'>
        <View className='card'>
          <View className='login-intro'>温柔疗愈 · 安心登录</View>
          <Text className='title'>💝 Between Us</Text>
          <Text className='login-subtitle'>让关系与情绪都有去处</Text>

          <View className='form'>
            <View className='input-group'>
              <Text className='label'>手机号</Text>
              <Input
                className='input-control'
                placeholder='请输入手机号'
                type='text'
                value={phone}
                onInput={(event) => setPhone(event.detail.value)}
              />
            </View>

            <View className='input-group'>
              <Text className='label'>密码</Text>
              <Input
                className='input-control'
                placeholder={isLogin ? '请输入密码' : '请设置密码'}
                type='password'
                value={password}
                onInput={(event) => setPassword(event.detail.value)}
                onConfirm={handleSubmit}
              />
            </View>

            {!isLogin && (
              <View className='input-group'>
                <Text className='label'>昵称（选填）</Text>
                <Input
                  className='input-control'
                  placeholder='不填默认为手机号后4位'
                  maxLength={20}
                  value={nickname}
                  onInput={(event) => setNickname(event.detail.value)}
                />
                <Text className='help-text'>最长20个字符</Text>
              </View>
            )}

            <Button
              className='btn btn-primary'
              loading={loading}
              onClick={handleSubmit}
            >
              {isLogin ? '登录' : '注册'}
            </Button>

            <Button
              className='btn btn-secondary'
              onClick={() => setIsLogin(!isLogin)}
            >
              {isLogin ? '注册新账号' : '返回登录'}
            </Button>

            <View className='link'>
              <Text>开始您的情感陪伴之旅 ❤️</Text>
            </View>
          </View>
        </View>
      </View>

      <View className='gentle-shape gentle-shape-1' />
      <View className='gentle-shape gentle-shape-2' />
      <View className='gentle-shape gentle-shape-3' />
    </View>
  )
}

export default LoginPage
