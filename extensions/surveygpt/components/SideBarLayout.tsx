'use client';

import classNames from 'classnames';
import React, { PropsWithChildren, useState } from 'react';

import SideBar from './SideBar';

const SideBarLayout = (props: PropsWithChildren) => {
  const [collapsed, setSidebarCollapsed] = useState(false);
  return (
    <div
      className={classNames({
        'grid border-r border-custom-gray-200 min-h-screen': true,
        'grid-cols-sidebar': !collapsed,
        'grid-cols-sidebar-collapsed': collapsed,
        '': collapsed,
        'transition-[grid-template-columns] duration-300 ease-in-out': true,
      })}
    >
      <SideBar
        collapsed={collapsed}
        setCollapsed={() => setSidebarCollapsed((prev) => !prev)}
      />
    </div>
  );
};

export default SideBarLayout;
