import axios, { AxiosInstance } from 'axios';
import { message, notification } from 'antd';

export interface Response<T = any> {
  success: boolean;
  content: T;
  message: string;
  status: string;
}

export class Api {
  private axios: AxiosInstance;

  constructor() {
    this.axios = axios.create();
    this.axios.interceptors.response.use((res) => {
      const data = res.data;
      if (!data.success) {
        notification.error({ message: data.message });
        throw new Error(data.message);
      }
      return data;
    });
  }

  async reviews(body: any) {
    body = {
      next: '0',
      record: false,
      loadMore: false,
      ...body,
    };
    let list = [];
    let { content } = await this.page(body);
    list = [].concat(content.liveList);
    let next = content.next;
    while (next !== body.next) {
      body.next = next;
      content = (await this.page(body)).content;
      next = content.next;
      list = list.concat(content.content);
    }
    return list;
  }

  async reviewsPage(body: any) {
    return this.page({
      record: true,
      loadMore: true,
      ...body,
    });
  }

  async lives() {
    const body = {
      next: 0,
      loadMore: false,
      record: false,
    };
    return await this.page(body);
  }

  async page(body: any) {
    return this.axios.post<any, Response>('/api/lives', body);
  }

  async getOne(body: any) {
    return this.axios.post<any, Response>('/api/live', body);
  }

  async information() {
    return this.axios.get<any, Response>('/api/info');
  }
}

export const ApiInstance = new Api();
