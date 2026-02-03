import { useState, useEffect, useCallback } from 'react';
import { getUserProfile, getUserPayments, getUserGifts } from '../api/client';
import type { User, Payment, GiftCode, ReceivedGift } from '../api/types';

// Хук для загрузки профиля пользователя
export function useUserProfile() {
  const [data, setData] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const profile = await getUserProfile();
      setData(profile);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

// Хук для загрузки платежей
export function usePayments() {
  const [data, setData] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getUserPayments();
      setData(result.payments || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

// Хук для загрузки подарков
export function useGifts() {
  const [purchased, setPurchased] = useState<GiftCode[]>([]);
  const [received, setReceived] = useState<ReceivedGift[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getUserGifts();
      setPurchased(result.purchasedGifts || []);
      setReceived(result.receivedGifts || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Ошибка загрузки');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { purchased, received, loading, error, refetch };
}

