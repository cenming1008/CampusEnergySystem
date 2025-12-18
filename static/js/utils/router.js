// 简单的路由分发器
export function initRouter(routes) {
    const links = document.querySelectorAll('.menu-item a');
    
    links.forEach(link => {
        link.addEventListener('click', async (e) => {
            e.preventDefault();
            const pageName = link.dataset.page;
            
            // 1. 视觉切换：高亮菜单
            document.querySelectorAll('.menu-item').forEach(li => li.classList.remove('active'));
            link.parentElement.classList.add('active');

            // 2. 执行路由回调
            if (routes[pageName]) {
                // 清理工作交给具体页面自己处理（如果有的话）
                await routes[pageName]();
            } else {
                console.warn(`页面 ${pageName} 尚未注册`);
            }
        });
    });
}