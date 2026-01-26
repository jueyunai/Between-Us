import React, { useEffect, useState, useRef } from 'react'
import { View, Text, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { Input, Button } from '@nutui/nutui-react-taro'
import { sendLoungeMessage, getLoungeMessages } from '../../services/api'
import { getUserInfo } from '../../utils/storage'
import './index.scss'

interface LoungeMessage {
  id: number
  user_id: number
  nickname: string
  message: string
  created_at: string
  is_ai?: boolean
}

const LoungePage: React.FC = () => {
  const [messages, setMessages] = useState<LoungeMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const pollRef = useRef<any>(null)
  const lastIdRef = useRef<number>(0)
  const user = getUserInfo()

  useEffect(() => {
    loadMessages()
    startPolling()

    return () => {
      stopPolling()
    }
  }, [])

  const loadMessages = async () => {
    const res = await getLoungeMessages()
    if (res.success && res.data?.messages) {
      setMessages(res.data.messages)
      if (res.data.messages.length > 0) {
        lastIdRef.current = res.data.messages[res.data.messages.length - 1].id
      }
      scrollToBottom()
    }
  }

  const startPolling = () => {
    pollRef.current = setInterval(async () => {
      const res = await getLoungeMessages(lastIdRef.current)
      if (res.success && res.data?.messages && res.data.messages.length > 0) {
        setMessages((prev) => [...prev, ...res.data.messages])
        lastIdRef.current = res.data.messages[res.data.messages.length - 1].id
        scrollToBottom()
      }
    }, 3000)
  }

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current)
      pollRef.current = null
    }
  }

  const scrollToBottom = () => {
    setTimeout(() => {
      Taro.pageScrollTo({ scrollTop: 99999, duration: 300 })
    }, 100)
  }

  const handleSend = async () => {
    const text = inputValue.trim()
    if (!text || loading) return

    const nickname = user?.nickname || '我'

    setLoading(true)
    setInputValue('')

    try {
      const res = await sendLoungeMessage(text, nickname)
      if (res.success) {
        // 立即获取新消息
        await loadMessages()
      } else {
        Taro.showToast({ title: res.message || '发送失败', icon: 'none' })
      }
    } finally {
      setLoading(false)
    }
  }

  const isMyMessage = (msg: LoungeMessage) => {
    return msg.user_id === user?.id
  }

  return (
    <View className='lounge-page'>
      <View className='lounge-header'>
        <Text className='header-icon'>💬</Text>
        <View className='header-info'>
          <Text className='header-title'>情感客厅</Text>
          <Text className='header-hint'>与伴侣一起畅聊，AI 也会参与互动</Text>
        </View>
      </View>

      <ScrollView className='lounge-messages' scrollY scrollWithAnimation>
        {messages.length === 0 ? (
          <View className='empty-state'>
            <Text className='empty-icon'>💑</Text>
            <Text className='empty-text'>开始你们的对话吧</Text>
            <Text className='empty-hint'>发送第一条消息，AI 也会加入互动哦</Text>
          </View>
        ) : (
          messages.map((msg) => (
            <View
              key={msg.id}
              className={`message-item ${isMyMessage(msg) ? 'mine' : msg.is_ai ? 'ai' : 'partner'}`}
            >
              {!isMyMessage(msg) && (
                <View className='message-nickname'>
                  {msg.is_ai ? '🤖 AI助手' : `💝 ${msg.nickname}`}
                </View>
              )}
              <View className='message-content'>
                {!isMyMessage(msg) && (
                  <View className='message-avatar'>
                    {msg.is_ai ? '🤖' : '💝'}
                  </View>
                )}
                <View className='message-bubble'>
                  <Text className='message-text'>{msg.message}</Text>
                </View>
                {isMyMessage(msg) && (
                  <View className='message-avatar mine'>
                    😊
                  </View>
                )}
              </View>
            </View>
          ))
        )}
      </ScrollView>

      <View className='lounge-input-area'>
        <Input
          className='lounge-input'
          placeholder='说点什么...'
          value={inputValue}
          onChange={(val) => setInputValue(val)}
          onConfirm={handleSend}
        />
        <Button
          className='send-btn'
          type='primary'
          size='small'
          loading={loading}
          disabled={!inputValue.trim()}
          onClick={handleSend}
        >
          发送
        </Button>
      </View>
    </View>
  )
}

export default LoungePage
