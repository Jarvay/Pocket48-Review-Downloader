import React, { useEffect, useState } from 'react';
import './App.css';
import { Layout, Menu, Skeleton } from 'antd';
import { Route, Routes, useNavigate } from 'react-router-dom';
import { routes as allRoutes } from './routes';
import { ApiInstance } from './services/api';
import Utils from './services/utils';

const { Sider, Content, Header } = Layout;

const routes = allRoutes.filter((item) => !item.hide);

function App() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    setLoading(true);
    ApiInstance.information()
      .then((result) => {
        Utils.setInformation(result.content);
        setLoading(false);
      })
      .catch((e) => {
        console.error(e);
        setLoading(false);
      });
  }, []);

  return (
    <Layout style={{ width: '100%', height: '100%' }}>
      <Sider>
        <Menu
          theme="dark"
          mode="inline"
          items={routes}
          onSelect={({ key }) => {
            const route = routes.find((item) => item.key === key);
            if (route?.path) {
              navigate(route.path);
            }
          }}
        />
      </Sider>

      <Layout>
        <Header style={{ backgroundColor: '#e5e5e5' }}></Header>
        <Content
          style={{
            height: '100%',
            overflowY: 'auto',
            overflowX: 'hidden',
            boxSizing: 'border-box',
            padding: '16px',
          }}
        >
          <Skeleton loading={loading}>
            <Routes>
              {allRoutes.map((route) => (
                <Route {...route} />
              ))}
            </Routes>
          </Skeleton>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
